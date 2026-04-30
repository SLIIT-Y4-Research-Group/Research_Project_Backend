from fastapi import APIRouter, HTTPException
from bson import ObjectId
from app.schemas.story.story import StoryCreate, Story
from app.services.story.story_service import story_service, serialize_story

router = APIRouter(prefix="/stories", tags=["stories"])


@router.post("/", response_model=Story)
async def create_story(story: StoryCreate):
    return await story_service.create_story(story)


@router.get("/user/{user_id}", response_model=list[Story])
async def get_user_stories(user_id: str, limit: int = 20):
    return await story_service.get_stories_by_user(user_id, limit)


@router.get("/public/", response_model=list[Story])
async def get_public_stories(limit: int = 20):
    return await story_service.get_public_stories(limit)


@router.get("/{story_id}", response_model=Story)
async def get_story(story_id: str):
    collection = story_service.get_collection()

    try:
        story = await collection.find_one({"_id": ObjectId(story_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid story ID")

    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    await story_service.increment_views(story_id)
    return Story(**serialize_story(story))
