from typing import Optional
from datetime import datetime
from app.database.db import db

def save_mood(userId: int, mood: str, datetime: datetime):
    mood_data = {
        "userId": userId,
        "mood": mood,
        "datetime": datetime
    }
    result = db.moods.insert_one(mood_data)
    mood_data["_id"] = str(result.inserted_id)
    return mood_data
