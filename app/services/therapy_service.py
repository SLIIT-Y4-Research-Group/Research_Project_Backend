"""
Therapy Engagement Service
Stores and retrieves child therapy session data
"""
from datetime import datetime, timedelta
from typing import List, Optional
from bson import ObjectId
import logging

from app.database.db import db

logger = logging.getLogger(__name__)

# Collection
therapy_sessions_col = db["therapy_sessions"]


def create_therapy_session(
    child_id: str,
    activity_type: str,
    duration_seconds: int,
    score: Optional[int] = None,
    rounds_completed: Optional[int] = None,
    triggered_by_emotion: Optional[str] = None,
) -> dict:
    """Store a completed therapy session"""
    doc = {
        "child_id": child_id,
        "activity_type": activity_type,          # "bubble_pop" | "breath_game"
        "duration_seconds": duration_seconds,
        "score": score,
        "rounds_completed": rounds_completed,
        "triggered_by_emotion": triggered_by_emotion,
        "created_at": datetime.utcnow(),
    }
    result = therapy_sessions_col.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def get_therapy_sessions_for_child(
    child_id: str,
    days: int = 30,
) -> List[dict]:
    """Get all therapy sessions for a child within the last N days"""
    since = datetime.utcnow() - timedelta(days=days)
    sessions = list(
        therapy_sessions_col.find(
            {"child_id": child_id, "created_at": {"$gte": since}}
        ).sort("created_at", 1)
    )
    for s in sessions:
        s["session_id"] = str(s.pop("_id"))
    return sessions


def get_therapy_summary_for_child(child_id: str, days: int = 30) -> dict:
    """Aggregated therapy engagement stats for report"""
    sessions = get_therapy_sessions_for_child(child_id, days=days)

    bubble_sessions = [s for s in sessions if s["activity_type"] == "bubble_pop"]
    breath_sessions = [s for s in sessions if s["activity_type"] == "breath_game"]

    total_duration = sum(s.get("duration_seconds", 0) for s in sessions)

    bubble_scores = [s["score"] for s in bubble_sessions if s.get("score") is not None]
    avg_score = round(sum(bubble_scores) / len(bubble_scores), 1) if bubble_scores else None

    last_session = sessions[-1]["created_at"] if sessions else None

    return {
        "total_sessions": len(sessions),
        "bubble_pop_sessions": len(bubble_sessions),
        "breath_game_sessions": len(breath_sessions),
        "total_duration_minutes": round(total_duration / 60, 1),
        "avg_bubble_pop_score": avg_score,
        "last_session_at": last_session,
        "sessions": sessions,   # full list for charting
    }


def ensure_indexes():
    therapy_sessions_col.create_index([("child_id", 1), ("created_at", -1)])
    therapy_sessions_col.create_index([("activity_type", 1)])


ensure_indexes()