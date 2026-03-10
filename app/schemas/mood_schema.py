from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MoodCheckin(BaseModel):
    child_id: int
    mood: str
    note: str | None = None

    class Config:
        from_attributes = True

class MoodData(BaseModel):
    userId: int
    mood: str
    datetime: datetime

    class Config:
        from_attributes = True

class MoodStoreRequest(BaseModel):
    """Request schema for /mood/store endpoint (child_id comes from JWT)"""
    mood: str
    datetime: datetime

    class Config:
        from_attributes = True

class MoodPredictRequest(BaseModel):
    text: str

class MoodQuestionPredictRequest(BaseModel):
    question_id: int
    text: str

class ValidateAnswerRequest(BaseModel):
    question_id: int
    text: str

class MoodOverallRequest(BaseModel):
    answers: list[str]

class AlertPermissionResponse(BaseModel):
    """Request schema for student responding to alert permission"""
    approve: bool

class TodayMoodStatusResponse(BaseModel):
    """Response schema for GET /child/me/today-mood-status"""
    completed: bool
    date: str
    mood: Optional[str] = None
    recorded_at: Optional[datetime] = None  # Fixed: renamed from 'datetime' to avoid collision

class WeeklyMoodDay(BaseModel):
    """Single day in weekly mood history"""
    date: str
    mood: Optional[str] = None
    completed: bool
    recorded_at: Optional[datetime] = None  # Fixed: renamed from 'datetime' to avoid collision

class WeeklyMoodSummary(BaseModel):
    """Summary statistics for weekly moods"""
    happy: int
    normal: int
    bad: int
    missed: int

class WeeklyMoodsResponse(BaseModel):
    """Response schema for GET /child/me/weekly-moods"""
    days: list[WeeklyMoodDay]
    summary: WeeklyMoodSummary
