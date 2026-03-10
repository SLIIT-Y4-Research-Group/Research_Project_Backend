from motor.motor_asyncio import AsyncIOMotorClient
from app.core.story.config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    def __init__(self):
        self.client: AsyncIOMotorClient | None = None
        self.database = None

    async def connect(self):
        try:
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=5000  # fail fast if cannot connect
            )
            await self.client.server_info()  # forces connection, raises if failed
            self.database = self.client[settings.MONGODB_DB_NAME]
            logger.info("MongoDB Atlas connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB Atlas: {e}")
            raise

    async def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB disconnected")

    def get_collection(self, collection_name: str):
        if self.database is None:
            raise RuntimeError("MongoDB not initialized. Call connect() first.")
        return self.database[collection_name]


mongodb = MongoDB()
