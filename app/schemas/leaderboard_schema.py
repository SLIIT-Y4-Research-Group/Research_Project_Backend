from datetime import datetime
from pydantic import BaseModel, Field


class LeaderboardCreateRequest(BaseModel):
    player_name: str = Field(..., min_length=1, max_length=100)
    score: int = Field(..., ge=0)
    level: int = Field(..., ge=0)
    time: float = Field(..., ge=0)


class LeaderboardEntryResponse(BaseModel):
    id: str
    player_name: str
    score: int
    level: int
    time: float
    created_at: datetime
