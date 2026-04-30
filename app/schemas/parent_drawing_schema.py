from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any

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