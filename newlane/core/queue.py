import rq
import redis

from newlane.config import settings

client = redis.Redis(settings.redis.host, settings.redis.port)
queue = rq.Queue(connection=client)
