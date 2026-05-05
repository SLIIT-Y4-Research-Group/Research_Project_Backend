"""
Therapy Engagement Schemas
Tracks child participation in therapeutic activities (bubble pop, breath game)
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TherapySessionCreate(BaseModel):
    """Sent by Flutter when a therapy session completes"""
    activity_type: str          # "bubble_pop" | "breath_game"
    duration_seconds: int       # How long the session lasted
    score: Optional[int] = None             # bubble_pop score
    rounds_completed: Optional[int] = None  # breath_game rounds
    triggered_by_emotion: Optional[str] = None  # "sad" — what caused the recommendation


class TherapySessionResponse(BaseModel):
    session_id: str
    child_id: str
    activity_type: str
    duration_seconds: int
    score: Optional[int] = None
    rounds_completed: Optional[int] = None
    triggered_by_emotion: Optional[str] = None
    created_at: datetime


class TherapyEngagementSummary(BaseModel):
    total_sessions: int
    bubble_pop_sessions: int
    breath_game_sessions: int
    total_duration_minutes: float
    avg_bubble_pop_score: Optional[float] = None
    last_session_at: Optional[datetime] = None