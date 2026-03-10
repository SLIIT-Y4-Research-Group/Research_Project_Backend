from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class MoodWheel(str, Enum):
    sad = "sad"
    anxious = "anxious"
    empty = "empty"
    calm = "calm"
    happy = "happy"
    angry = "angry"
    confused = "confused"
    hopeful = "hopeful"

class WeatherMetaphor(str, Enum):
    sunny = "sunny"
    rainy = "rainy"
    stormy = "stormy"
    foggy = "foggy"

class FolkTaleCharacter(str, Enum):
    hare = "hare"
    lion = "lion"
    elephant = "elephant"

class MoodProfile(BaseModel):
    mood: MoodWheel
    weather: WeatherMetaphor
    character: FolkTaleCharacter
    starter_sentence: Optional[str] = None

class StoryBase(BaseModel):
    user_id: str
    title: str
    content: str
    mood_profile: MoodProfile
    tags: List[str] = []
    is_public: bool = True

class StoryCreate(StoryBase):
    pass

class Story(StoryBase):
    id: str = Field(alias="_id")
    like_count: int = 0
    view_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
        populate_by_name = True