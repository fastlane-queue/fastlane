import functools

from rq import Queue
from redis import Redis
from docker import DockerClient
from odmantic import AIOEngine
from rq_scheduler import Scheduler
from motor.motor_asyncio import AsyncIOMotorClient

from newlane.config import settings


@functools.cache
def get_db():
    client = AsyncIOMotorClient(settings.mongo)
    return AIOEngine(motor_client=client, database='fastlane')


@functools.cache
def get_docker():
    return DockerClient(base_url=settings.docker)


@functools.cache
def get_queue():
    client = Redis(settings.redis.host, settings.redis.port)
    return Queue(connection=client)


@functools.cache
def get_scheduler():
    client = Redis(settings.redis.host, settings.redis.port)
    return Scheduler(connection=client)
