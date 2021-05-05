import rq
import redis
import rq_scheduler

from newlane.config import settings

client = redis.Redis(settings.redis.host, settings.redis.port)
queue = rq.Queue(connection=client)
scheduler = rq_scheduler.Scheduler(connection=client)
