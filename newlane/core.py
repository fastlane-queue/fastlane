from rq import Queue
from redis import Redis
from docker import DockerClient
from odmantic import AIOEngine
from rq_scheduler import Scheduler
from motor.motor_asyncio import AsyncIOMotorClient

from newlane.config import settings

_db = None
_docker = None
_queue = None
_scheduler = None


def get_db():
    global _db
    if _db is not None:
        return _db
    client = AsyncIOMotorClient(settings.mongo)
    _db = AIOEngine(motor_client=client, database='fastlane')
    return _db


def get_docker():
    global _docker
    if _docker is not None:
        return _docker
    _docker = DockerClient(base_url=settings.docker)
    return _docker


def get_queue():
    global _queue
    if _queue is not None:
        return _queue
    client = Redis(settings.redis.host, settings.redis.port)
    _queue = Queue(connection=client)
    return _queue


def get_scheduler():
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    client = Redis(settings.redis.host, settings.redis.port)
    _scheduler = Scheduler(connection=client)
    return _scheduler
