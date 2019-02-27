# Standard Library
from datetime import datetime, timezone
from uuid import uuid4

# 3rd Party
from flask import current_app

# Fastlane
from fastlane.models.categories import Categories
from fastlane.utils import dumps, get_next_cron_timestamp, loads, parse_time, to_unix
from fastlane.worker.job import monitor_job, run_job, send_email, send_webhook


class Message:
    def __init__(self, queue, category, *args, **kw):
        self.queue = queue
        self.category = category

        if "id" in kw:
            self.id = kw.pop("id")  # pylint: disable=invalid-name
        else:
            self.id = str(uuid4())

        self.args = args
        self.kwargs = kw

    def serialize(self):
        return dumps(self)

    @classmethod
    def deserialize(cls, data):
        instance = Message("", "")
        instance.__dict__ = loads(  # pylint: disable=attribute-defined-outside-init
            data
        )

        return instance

    def run(self):
        if self.category == Categories.Job:
            current_app.logger.debug("Running job...")
            run_job(*self.args, **self.kwargs)

        if self.category == Categories.Monitor:
            current_app.logger.debug("Running Monitoring...")
            monitor_job(*self.args, **self.kwargs)

        if self.category == Categories.Webhook:
            current_app.logger.debug("Running Webhook...")
            send_webhook(*self.args, **self.kwargs)

        if self.category == Categories.Notify:
            current_app.logger.debug("Running Notification...")
            send_email(*self.args, **self.kwargs)


class QueueGroup:
    def __init__(self, redis, queues):
        self.queues = queues
        self.redis = redis

    def dequeue(self, queues=None, timeout=1):
        queues_to_pop = []

        if queues is None:
            queues_to_pop = [q.queue_name for q in self.queues]
        else:
            queues_to_pop = [q.queue_name for q in self.queues if q.queue_id in queues]

        result = self.redis.blpop(queues_to_pop, timeout=max(timeout, 1))

        if result is None:
            return None

        _, item = result

        return Message.deserialize(item.decode("utf-8"))

    def move_jobs(self):
        lock = self.redis.lock(
            Queue.MOVE_JOBS_LOCK_NAME,
            timeout=5,
            sleep=0.1,
            blocking_timeout=500,
            thread_local=False,
        )

        if not lock.acquire():
            return None

        moved_items = []

        try:
            timestamp = to_unix(datetime.utcnow())

            pipe = self.redis.pipeline()
            pipe.zrangebyscore(Queue.SCHEDULED_QUEUE_NAME, "-inf", timestamp)
            pipe.zremrangebyscore(Queue.SCHEDULED_QUEUE_NAME, "-inf", timestamp)
            items, _ = pipe.execute()

            for message_id in items:
                key = Queue.get_message_name(message_id.decode("utf-8"))
                data = self.redis.get(key)
                msg = Message.deserialize(data.decode("utf-8"))
                pipe = self.redis.pipeline()
                pipe.lpush(msg.queue, msg.serialize())
                pipe.delete(key)
                pipe.execute()
                moved_items.append(msg)

            return moved_items
        finally:
            lock.release()


class Queue:
    QUEUE_NAME = "fastlane:message-queue"
    SCHEDULED_QUEUE_NAME = "fastlane:scheduled-messages:items"
    MOVE_JOBS_LOCK_NAME = "fastlane:move-jobs-lock"
    SCHEDULED_MESSAGE_NAME = "fastlane:scheduled-message"

    def __init__(self, redis, queue_name="main"):
        self.redis = redis
        self.queue_id = queue_name
        self.queue_name = f"{Queue.QUEUE_NAME}:{queue_name}"

    def enqueue(self, category, *args, **kw):
        msg = Message(self.queue_name, category, *args, **kw)

        return self.__enqueue(msg)

    def __enqueue(self, msg):
        self.redis.lpush(self.queue_name, msg.serialize())

        return msg.id

    @classmethod
    def get_message_name(cls, message_id):
        return f"{Queue.SCHEDULED_MESSAGE_NAME}:{message_id}"

    def enqueue_at(self, timestamp, category, *args, **kw):
        return self.__enqueue_at_timestamp(timestamp, category, *args, **kw)

    def enqueue_in(self, incr, category, *args, **kw):
        start_in = parse_time(incr)
        future_date = datetime.now(tz=timezone.utc) + start_in
        timestamp = to_unix(future_date)

        return self.__enqueue_at_timestamp(timestamp, category, *args, **kw)

    def enqueue_cron(self, cron, category, *args, **kw):
        next_dt = get_next_cron_timestamp(cron)
        timestamp = to_unix(next_dt)

        return self.__enqueue_at_timestamp(timestamp, category, *args, **kw)

    def __enqueue_at_timestamp(self, timestamp, category, *args, **kw):
        msg = Message(self.queue_name, category, *args, **kw)

        pipe = self.redis.pipeline()
        pipe.set(self.get_message_name(msg.id), msg.serialize())
        pipe.zadd(Queue.SCHEDULED_QUEUE_NAME, timestamp, msg.id)
        pipe.execute()

        return msg.id

    def dequeue(self, blocking=False, timeout=1):
        if blocking:
            result = self.redis.blpop(self.queue_name, timeout=max(timeout, 1))

            if result is None:
                return None
            _, item = result
        else:
            item = self.redis.lpop(self.queue_name)

        if item is None:
            return None

        return Message.deserialize(item.decode("utf-8"))

    def is_scheduled(self, message_id):
        return self.redis.exists(self.get_message_name(message_id))

    def deschedule(self, message_id):
        pipe = self.redis.pipeline()
        pipe.zrem(Queue.SCHEDULED_QUEUE_NAME, message_id)
        pipe.delete(self.get_message_name(message_id))
        results = pipe.execute()

        return results[0] == 1
