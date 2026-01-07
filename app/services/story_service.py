from app.database.mongo import mongodb
from app.schemas.story import StoryCreate, Story
from bson import ObjectId
from datetime import datetime


def serialize_story(story: dict) -> dict:
    story["id"] = str(story["_id"])
    del story["_id"]
    return story


class StoryService:
    def get_collection(self):
        return mongodb.get_collection("stories")

    async def create_story(self, story_data: StoryCreate) -> Story:
        collection = self.get_collection()

        story_dict = story_data.model_dump()
        story_dict["created_at"] = datetime.utcnow()
        story_dict["updated_at"] = datetime.utcnow()

        result = await collection.insert_one(story_dict)
        created_story = await collection.find_one(
            {"_id": result.inserted_id}
        )

        return Story(**serialize_story(created_story))

    async def get_stories_by_user(self, user_id: str, limit: int = 20):
        collection = self.get_collection()

        cursor = (
            collection.find({"user_id": user_id})
            .sort("created_at", -1)
            .limit(limit)
        )
        stories = await cursor.to_list(length=limit)

        return [Story(**serialize_story(story)) for story in stories]

    async def get_public_stories(self, limit: int = 20):
        collection = self.get_collection()

        cursor = (
            collection.find({"is_public": True})
            .sort("created_at", -1)
            .limit(limit)
        )
        stories = await cursor.to_list(length=limit)

        return [Story(**serialize_story(story)) for story in stories]

    async def increment_views(self, story_id: str):
        collection = self.get_collection()

        await collection.update_one(
            {"_id": ObjectId(story_id)},
            {"$inc": {"view_count": 1}}
        )


story_service = StoryService()
