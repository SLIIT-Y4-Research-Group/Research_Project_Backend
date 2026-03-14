from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


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
    """Response for a single track"""
    id: str
    title: str
    artist: str
    emotions: List[str]
    music_url: str
    cover_url: str
    created_at: datetime
    uploader: TrackUploader


class TracksListResponse(BaseModel):
    """Response for list of tracks"""
    tracks: List[TrackResponse]
    count: int
