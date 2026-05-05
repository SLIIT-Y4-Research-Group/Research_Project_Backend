from typing import Any, Dict, Optional, List
from pydantic import BaseModel
from datetime import datetime


class DrawingAnalysisResponse(BaseModel):
    status: str
    analysis_id: str
    child_id: str
    created_at: datetime
    source_mode: str
    emotion: Dict[str, Any]
    color: Dict[str, Any]
    stroke: Dict[str, Any]
    spatial: Dict[str, Any]
    objects: Optional[Dict[str, Any]] = None
    llm_review: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class ParentChildDrawingItem(BaseModel):
    analysis_id: str
    child_id: str
    child_name: str
    child_username: str
    created_at: datetime
    note: Optional[str] = None
    filename: Optional[str] = None
    content_type: Optional[str] = None
    source_mode: Optional[str] = None
    emotion: Optional[dict[str, Any]] = None
    color: Optional[dict[str, Any]] = None
    stroke: Optional[dict[str, Any]] = None
    spatial: Optional[dict[str, Any]] = None
    objects: Optional[Any] = None
    llm_review: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    image_base64: Optional[str] = None


class ChildGalleryItem(BaseModel):
    analysis_id: str
    created_at: datetime
    filename: Optional[str] = None
    source_mode: Optional[str] = None
    emotion_label: Optional[str] = None
    image_base64: Optional[str] = None