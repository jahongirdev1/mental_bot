from motor.motor_asyncio import AsyncIOMotorClient

from config import settings


client = AsyncIOMotorClient(settings.MONGO_URL)
database = client[settings.DB_NAME]
checkins_collection = database["checkins"]
stress_collection = database["stress_tests"]
