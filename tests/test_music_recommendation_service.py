from datetime import datetime, timedelta, timezone

import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.services import music_recommendation_service as svc


class FakeCollection:
    def __init__(self):
        self.docs = []

    def insert_one(self, doc):
        new_doc = dict(doc)
        new_doc["_id"] = ObjectId()
        self.docs.append(new_doc)
        return type("R", (), {"inserted_id": new_doc["_id"]})()

    def find_one(self, query, projection=None):
        for d in self.docs:
            ok = True
            for k, v in query.items():
                if d.get(k) != v:
                    ok = False
                    break
            if ok:
                return d
        return None

    def update_one(self, query, update):
        d = self.find_one(query)
        if d:
            d.update(update.get("$set", {}))

    def find(self, query=None, projection=None):
        query = query or {}
        result = []
        for d in self.docs:
            ok = True
            for k, v in query.items():
                if isinstance(v, dict) and "$ne" in v:
                    if d.get(k) == v["$ne"]:
                        ok = False
                        break
                elif isinstance(v, dict) and "$in" in v:
                    if not any(item in d.get(k, []) for item in v["$in"]):
                        ok = False
                        break
                else:
                    if d.get(k) != v:
                        ok = False
                        break
            if ok:
                result.append(d)
        return FakeCursor(result)


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, key, direction):
        reverse = direction == -1
        self.docs.sort(key=lambda x: x.get(key), reverse=reverse)
        return self.docs


@pytest.fixture
def setup_fakes(monkeypatch):
    tracks = FakeCollection()
    sessions = FakeCollection()
    monkeypatch.setattr(svc, "tracks_col", tracks)
    monkeypatch.setattr(svc, "music_sessions_col", sessions)
    monkeypatch.setattr(svc, "_emotion_snapshot_from_image", lambda img: {"emotion_idx": 3, "emotion_label": img, "confidence": 0.9})
    return tracks, sessions


def test_start_and_complete_session(setup_fakes):
    tracks, sessions = setup_fakes
    t = {"_id": ObjectId(), "title": "A", "artist": "B", "emotions": ["sad"], "created_at": datetime.now(timezone.utc)}
    tracks.docs.append(t)

    started = svc.start_music_session("u1", str(t["_id"]), "sad")
    assert started["before_emotion"]["emotion_label"] == "sad"

    completed = svc.complete_music_session(str(started["_id"]), "u1", "happy", 5)
    assert completed["ended_at"] is not None
    assert completed["impact_score"] >= 0


def test_complete_session_rejects_double_complete(setup_fakes):
    tracks, _sessions = setup_fakes
    t = {"_id": ObjectId(), "title": "A", "artist": "B", "emotions": ["sad"], "created_at": datetime.now(timezone.utc)}
    tracks.docs.append(t)
    started = svc.start_music_session("u1", str(t["_id"]), "sad")
    svc.complete_music_session(str(started["_id"]), "u1", "happy", 4)
    with pytest.raises(HTTPException) as exc:
        svc.complete_music_session(str(started["_id"]), "u1", "happy", 4)
    assert exc.value.status_code == 409


def test_recommendation_ranking_prefers_high_impact(setup_fakes):
    tracks, sessions = setup_fakes
    t1 = {"_id": ObjectId(), "title": "Top", "artist": "A", "emotions": ["sad"], "created_at": datetime.now(timezone.utc)}
    t2 = {"_id": ObjectId(), "title": "Low", "artist": "B", "emotions": ["sad"], "created_at": datetime.now(timezone.utc) - timedelta(days=1)}
    tracks.docs.extend([t1, t2])
    now = datetime.now(timezone.utc)
    sessions.docs.extend(
        [
            {
                "_id": ObjectId(),
                "user_id": "u1",
                "track_id": str(t1["_id"]),
                "ended_at": now,
                "impact_score": 0.95,
                "satisfaction_rating": 5,
                "improvement_score": 0.9,
            },
            {
                "_id": ObjectId(),
                "user_id": "u1",
                "track_id": str(t2["_id"]),
                "ended_at": now,
                "impact_score": 0.2,
                "satisfaction_rating": 2,
                "improvement_score": 0.2,
            },
        ]
    )
    ranked = svc.personalized_recommendations("u1", "sad")
    assert ranked[0]["title"] == "Top"
