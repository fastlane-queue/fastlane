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
    MESSAGE_DETAILS_NAME = "fastlane:scheduled-message"
    MESSAGE_HASH_NAME = "fastlane:message-queue-ids"

    def __init__(self, queue, category, cron_str, *args, **kw):
        self.queue = queue
        self.category = category
        self.cron_str = cron_str

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
        instance = Message("", "", None)
        instance.__dict__ = loads(  # pylint: disable=attribute-defined-outside-init
            data
        )

        return instance

    def message_hash_key(self):
        return self.generate_message_hash_key(self.queue)

    def message_key(self):
        return self.generate_message_key(self.id)

    @classmethod
    def generate_message_key(cls, message_id):
        return f"{Message.MESSAGE_DETAILS_NAME}:{message_id}"

    @classmethod
    def generate_message_hash_key(cls, queue):
        return f"{Message.MESSAGE_HASH_NAME}:{queue}"

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
    def __init__(self, logger, redis, queues):
        self.logger = logger
        self.queues = queues
        self.redis = redis

    def dequeue(self, queues=None, timeout=1):
        queues_to_pop = []

        if queues is None:
            queues_to_pop = [q.queue_name for q in self.queues]
        else:
            queues_to_pop = [q.queue_name for q in self.queues if q.queue_id in queues]

        queue_executor = QueueExecutor(redis=self.redis, logger=self.logger)
        return queue_executor.dequeue_message(queues_to_pop, blocking=True, timeout=timeout)

    def move_jobs(self):
        logger = self.logger.bind(operation="move_jobs")

        lock = self.redis.lock(
            Queue.MOVE_JOBS_LOCK_NAME,
            timeout=5,
            sleep=0.1,
            blocking_timeout=500,
            thread_local=False,
        )

        if not lock.acquire():
            logger.info("Lock could not be acquired. Trying to move jobs again later.")

            return None

        moved_items = []

        try:
            timestamp = to_unix(datetime.utcnow())

            pipe = self.redis.pipeline()
            pipe.zrangebyscore(Queue.SCHEDULED_QUEUE_NAME, "-inf", timestamp)
            pipe.zremrangebyscore(Queue.SCHEDULED_QUEUE_NAME, "-inf", timestamp)
            items, _ = pipe.execute()

            if not items:
                logger.info("No jobs in need of moving right now.")

                return moved_items

            logger.info("Found jobs in need of moving.", job_count=len(items))

            for message_id in items:
                key = Message.generate_message_key(message_id.decode("utf-8"))
                data = self.redis.get(key)
                message = Message.deserialize(data.decode("utf-8"))
                logger.info(
                    "Moving job to queue.",
                    queue_name=message.queue,
                    job_id=message.id,
                    msg=message.serialize(),
                )
                queue_executor = QueueExecutor(redis=self.redis, logger=self.logger)
                queue_executor.enqueue_message(message)
                moved_items.append(message)

            logger.info("Moved jobs successfully.")

            return moved_items
        finally:
            lock.release()


class Queue:
    QUEUE_NAME = "fastlane:message-queue"
    SCHEDULED_QUEUE_NAME = "fastlane:scheduled-messages:items"
    MOVE_JOBS_LOCK_NAME = "fastlane:move-jobs-lock"

    def __init__(self, logger, redis, queue_name="main"):
        self.redis = redis
        self.queue_id = queue_name
        self.queue_name = f"{Queue.QUEUE_NAME}:{queue_name}"
        self.logger = logger.bind(queue_id=self.queue_id, queue_name=self.queue_name)

    def enqueue(self, category, *args, **kw):
        message = Message(self.queue_name, category, None, *args, **kw)

        self.logger.info(
            "Sending message to queue.", operation="enqueue", category=category
        )

        queue_executor = QueueExecutor(redis=self.redis, logger=self.logger)
        queue_executor.enqueue_message(message)

        return message.id

    def enqueue_at(self, timestamp, category, *args, **kw):
        return self.__enqueue_at_timestamp(timestamp, category, None, *args, **kw)

    def enqueue_in(self, incr, category, *args, **kw):
        start_in = parse_time(incr)
        future_date = datetime.now(tz=timezone.utc) + start_in
        timestamp = to_unix(future_date)

        return self.__enqueue_at_timestamp(timestamp, category, None, *args, **kw)

    def enqueue_cron(self, cron, category, *args, **kw):
        next_dt = get_next_cron_timestamp(cron)
        timestamp = to_unix(next_dt)

        return self.__enqueue_at_timestamp(timestamp, category, cron, *args, **kw)

    def dequeue(self, blocking=False, timeout=1):
        queue_executor = QueueExecutor(redis=self.redis, logger=self.logger)
        return queue_executor.dequeue_message(self.queue_name, blocking=blocking, timeout=timeout)

    def is_scheduled(self, message_id):
        return self.redis.zrank(Queue.SCHEDULED_QUEUE_NAME, message_id) is not None

    def is_enqueued(self, message_id):
        message_hash_key = Message.generate_message_hash_key(self.queue_name)
        return self.redis.zrank(message_hash_key, message_id) is not None

    def deschedule(self, message_id):
        logger = self.logger.bind(operation="deschedule", message_id=message_id)
        logger.info("Descheduling job from queue.")
        pipe = self.redis.pipeline()
        pipe.zrem(Queue.SCHEDULED_QUEUE_NAME, message_id)
        pipe.delete(Message.generate_message_key(message_id))
        results = pipe.execute()

        if results[0] == 1:
            logger.info("Descheduling job successful.")
        else:
            logger.info("Descheduling job failed (maybe job was not found).")

        return results[0] == 1

    def __enqueue_at_timestamp(self, timestamp, category, cron_str, *args, **kw):
        if not isinstance(timestamp, (int,)):
            raise RuntimeError(
                f"timestamp must be a UTC Unix Timestamp (integer), not {type(timestamp)}"
            )

        message = Message(self.queue_name, category, cron_str, *args, **kw)
        queue_executor = QueueExecutor(redis=self.redis, logger=self.logger)
        return queue_executor.enqueue_at_timestamp(message, timestamp)



class QueueExecutor:

    def __init__(self, redis, logger):
        self.redis = redis
        self.logger = logger

    def enqueue_message(self, message):
        timestamp = to_unix(datetime.utcnow())

        pipe = self.redis.pipeline()
        pipe.set(message.message_key(), message.serialize())
        pipe.zadd(message.message_hash_key(), {message.id: timestamp})
        pipe.lpush(message.queue, message.id)

        if message.cron_str:
            next_dt = get_next_cron_timestamp(message.cron_str)
            timestamp = to_unix(next_dt)
            msg_schedule = Message(message.queue, message.category, message.cron_str,
                                    *message.args, **message.kwargs)

            self._pipe_at_timestamp(pipe, msg_schedule, timestamp)

        return pipe.execute()

    def enqueue_at_timestamp(self, message, timestamp):
        pipe = self.redis.pipeline()
        self._pipe_at_timestamp(pipe, message, timestamp)
        pipe.execute()

        return message.id

    def _pipe_at_timestamp(self, pipe, message, timestamp):
        self.logger.info(
            "Scheduling message to run at future time.",
            operation="schedule",
            timestamp=timestamp,
            category=message.category,
        )

        pipe.set(message.message_key(), message.serialize())
        pipe.zadd(Queue.SCHEDULED_QUEUE_NAME, {message.id: timestamp})


    def dequeue_message(self, queue_names, blocking=False, timeout=1):
        queue = ""

        if isinstance(queue_names, (tuple, list)) or blocking:
            result = self.redis.blpop(queue_names, timeout=max(timeout, 1))

            if result is None:
                return None

            queue, item = result
        else:
            item = self.redis.lpop(queue_names)
            queue = queue_names[0]

        if item is None:
            return None

        msg_id = item.decode("utf-8")

        pipe = self.redis.pipeline()
        message_key = Message.generate_message_key(msg_id)
        message_hash_key = Message.generate_message_hash_key(queue)
        pipe.zrem(message_hash_key, msg_id)
        pipe.get(message_key)
        pipe.delete(message_key)
        _, message_data, _ = pipe.execute()

        return Message.deserialize(message_data.decode("utf-8"))
