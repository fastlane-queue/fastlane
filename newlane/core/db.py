from motor.motor_asyncio import AsyncIOMotorClient

from odmantic import AIOEngine

from newlane.config import settings

client = AsyncIOMotorClient(settings.mongo)
db = AIOEngine(motor_client=client, database='fastlane')
