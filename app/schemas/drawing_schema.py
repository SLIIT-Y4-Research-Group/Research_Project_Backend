from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime

class DrawingAnalysisResponse(BaseModel):
    status: str = "success"
    analysis_id: str
    child_id: int
    created_at: datetime

    emotion: Dict[str, Any]
    color: Dict[str, Any]
    stroke: Dict[str, Any]
    spatial: Dict[str, Any]
    objects: Optional[Dict[str, Any]] = None

class DrawingAnalysisMeta(BaseModel):
    child_id: int = Field(..., ge=1)
    note: Optional[str] = None