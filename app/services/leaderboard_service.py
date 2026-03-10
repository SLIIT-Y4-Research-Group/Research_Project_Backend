"""
Leaderboard Service
CRUD for game leaderboard entries
"""
from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from fastapi import HTTPException, status
from app.database.db import leaderboard_col


def create_entry(player_name: str, score: int, level: int, time: float) -> dict:
    entry = {
        "player_name": player_name,
        "score": score,
        "level": level,
        "time": time,
        "created_at": datetime.utcnow()
    }
    result = leaderboard_col.insert_one(entry)
    entry["_id"] = result.inserted_id
    return entry


def get_entry(entry_id: str) -> Optional[dict]:
    if not ObjectId.is_valid(entry_id):
        return None
    return leaderboard_col.find_one({"_id": ObjectId(entry_id)})


def list_entries(skip: int, limit: int) -> List[dict]:
    cursor = leaderboard_col.find().sort(
        [("score", -1), ("time", 1), ("created_at", -1)]
    ).skip(skip).limit(limit)
    return list(cursor)


def list_top(limit: int) -> List[dict]:
    cursor = leaderboard_col.find().sort(
        [("score", -1), ("time", 1), ("created_at", -1)]
    ).limit(limit)
    return list(cursor)


def list_by_player(player_name: str, skip: int, limit: int) -> List[dict]:
    cursor = leaderboard_col.find(
        {"player_name": player_name}
    ).sort([("score", -1), ("time", 1), ("created_at", -1)]).skip(skip).limit(limit)
    return list(cursor)


def delete_entry(entry_id: str) -> None:
    if not ObjectId.is_valid(entry_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid entry id"
        )
    result = leaderboard_col.delete_one({"_id": ObjectId(entry_id)})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
