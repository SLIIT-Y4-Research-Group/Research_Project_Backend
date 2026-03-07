from pydantic import BaseModel
from datetime import datetime

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
