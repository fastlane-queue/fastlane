import rq
import redis
import docker
import rq_scheduler
from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient

from newlane.config import settings

_db = None
_docker = None
_queue = None
_scheduler = None


def get_db():
    if _db is not None:
        return _db
    client = AsyncIOMotorClient(settings.mongo)
    return AIOEngine(motor_client=client, database='fastlane')


def get_docker():
    if _docker is not None:
        return _docker
    return docker.DockerClient(base_url=settings.docker)


def get_queue():
    if _queue is not None:
        return _queue
    client = redis.Redis(settings.redis.host, settings.redis.port)
    return rq.Queue(connection=client)


def get_scheduler():
    if _scheduler is not None:
        return _scheduler
    client = redis.Redis(settings.redis.host, settings.redis.port)
    return rq_scheduler.Scheduler(connection=client)
