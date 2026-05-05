from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class TrackUploader(BaseModel):
    id: str
    role: str
    email: Optional[str] = None
    username: Optional[str] = None


class TrackCreateResponse(BaseModel):
    id: str
    title: str
    artist: str
    emotions: List[str]
    music_url: str
    cover_url: str
    created_at: datetime
    uploader: TrackUploader


class TrackResponse(BaseModel):
    id: str
    title: str
    artist: str
    emotions: List[str]
    music_url: str
    cover_url: Optional[str] = None
    created_at: datetime


class EmotionSnapshot(BaseModel):
    emotion_idx: int
    emotion_label: str
    confidence: float


class StartMusicSessionRequest(BaseModel):
    track_id: str
    before_image: str


class StartMusicSessionResponse(BaseModel):
    session_id: str
    track_id: str
    user_id: str
    started_at: datetime
    before_emotion: EmotionSnapshot


class CompleteMusicSessionRequest(BaseModel):
    after_image: str
    satisfaction_rating: int = Field(..., ge=1, le=5)


class CompleteMusicSessionResponse(BaseModel):
    session_id: str
    track_id: str
    user_id: str
    started_at: datetime
    ended_at: datetime
    before_emotion: EmotionSnapshot
    after_emotion: EmotionSnapshot
    satisfaction_rating: int
    emotion_changed: bool
    improvement_score: float
    impact_score: float


class PersonalizedTrackResponse(TrackResponse):
    recommendation_score: float
