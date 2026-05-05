from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from bson import ObjectId

from app.database.db import music_sessions_col, tracks_col
from app.services.emotion_image_service import predict_emotion_from_base64

EMOTION_POSITIVITY = {
    "angry": 0.1,
    "disgust": 0.1,
    "fear": 0.2,
    "sad": 0.2,
    "neutral": 0.5,
    "surprise": 0.6,
    "happy": 1.0,
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _emotion_snapshot_from_image(image_b64: str) -> Dict:
    idx, label, confidence = predict_emotion_from_base64(image_b64)
    return {"emotion_idx": idx, "emotion_label": label, "confidence": confidence}


def _positivity_delta(before_label: str, after_label: str) -> float:
    return EMOTION_POSITIVITY.get(after_label.lower(), 0.5) - EMOTION_POSITIVITY.get(before_label.lower(), 0.5)


def _compute_scores(before_label: str, after_label: str, satisfaction_rating: int) -> Tuple[bool, float, float]:
    delta = _positivity_delta(before_label, after_label)
    improvement_score = max(0.0, min(1.0, (delta + 1.0) / 2.0))
    rating_score = satisfaction_rating / 5.0
    impact_score = 0.6 * rating_score + 0.4 * improvement_score
    emotion_changed = before_label.lower() != after_label.lower()
    return emotion_changed, improvement_score, impact_score


def start_music_session(user_id: str, track_id: str, before_image: str) -> Dict:
    if not ObjectId.is_valid(track_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid track id")
    track = tracks_col.find_one({"_id": ObjectId(track_id)})
    if not track:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track not found")

    before_emotion = _emotion_snapshot_from_image(before_image)
    now = _utcnow()
    session_doc = {
        "user_id": user_id,
        "track_id": track_id,
        "started_at": now,
        "ended_at": None,
        "before_emotion": before_emotion,
        "after_emotion": None,
        "satisfaction_rating": None,
        "emotion_changed": None,
        "improvement_score": None,
        "impact_score": None,
    }
    result = music_sessions_col.insert_one(session_doc)
    session_doc["_id"] = result.inserted_id
    return session_doc


def complete_music_session(session_id: str, user_id: str, after_image: str, satisfaction_rating: int) -> Dict:
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session id")
    session = music_sessions_col.find_one({"_id": ObjectId(session_id), "user_id": user_id})
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.get("ended_at") is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session already completed")

    after_emotion = _emotion_snapshot_from_image(after_image)
    before_label = session["before_emotion"]["emotion_label"]
    after_label = after_emotion["emotion_label"]
    emotion_changed, improvement_score, impact_score = _compute_scores(before_label, after_label, satisfaction_rating)
    now = _utcnow()
    update = {
        "$set": {
            "ended_at": now,
            "after_emotion": after_emotion,
            "satisfaction_rating": satisfaction_rating,
            "emotion_changed": emotion_changed,
            "improvement_score": improvement_score,
            "impact_score": impact_score,
        }
    }
    music_sessions_col.update_one({"_id": session["_id"]}, update)
    session.update(update["$set"])
    return session


def _candidate_tracks(current_emotion: Optional[str]) -> List[Dict]:
    query: Dict = {}
    if current_emotion:
        query["emotions"] = {"$in": [current_emotion.strip()]}
    return list(tracks_col.find(query).sort("created_at", -1))


def _fetch_user_track_stats(user_id: str) -> Dict[str, Dict[str, float]]:
    sessions = list(
        music_sessions_col.find(
            {"user_id": user_id, "ended_at": {"$ne": None}, "impact_score": {"$ne": None}},
            {"track_id": 1, "impact_score": 1, "satisfaction_rating": 1, "improvement_score": 1, "ended_at": 1},
        )
    )
    if not sessions:
        return {}

    now = _utcnow()
    stats: Dict[str, Dict[str, float]] = {}
    for s in sessions:
        tid = s["track_id"]
        ended_at = s.get("ended_at") or now
        age_days = max(0.0, (now - ended_at).total_seconds() / 86400.0)
        recency_weight = 1.0 / (1.0 + age_days / 7.0)
        bucket = stats.setdefault(tid, {"w": 0.0, "impact": 0.0, "satisfaction": 0.0, "improvement": 0.0, "count": 0.0})
        bucket["w"] += recency_weight
        bucket["impact"] += float(s.get("impact_score", 0.0)) * recency_weight
        bucket["satisfaction"] += (float(s.get("satisfaction_rating", 0.0)) / 5.0) * recency_weight
        bucket["improvement"] += float(s.get("improvement_score", 0.0)) * recency_weight
        bucket["count"] += 1.0
    return stats


def personalized_recommendations(user_id: str, current_emotion: Optional[str]) -> List[Dict]:
    tracks = _candidate_tracks(current_emotion)
    if not tracks:
        return []

    stats = _fetch_user_track_stats(user_id)
    if not stats:
        for t in tracks:
            t["recommendation_score"] = 0.5
        return tracks

    for t in tracks:
        tid = str(t["_id"])
        track_stats = stats.get(tid)
        if not track_stats:
            t["recommendation_score"] = 0.45
            continue
        w = max(track_stats["w"], 1e-6)
        avg_impact = track_stats["impact"] / w
        avg_satisfaction = track_stats["satisfaction"] / w
        avg_improvement = track_stats["improvement"] / w
        confidence_boost = min(0.1, 0.02 * track_stats["count"])
        t["recommendation_score"] = (0.5 * avg_impact) + (0.3 * avg_satisfaction) + (0.2 * avg_improvement) + confidence_boost

    tracks.sort(key=lambda x: x.get("recommendation_score", 0.0), reverse=True)
    return tracks

