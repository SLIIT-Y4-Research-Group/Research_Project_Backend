from typing import Any, Dict, Optional
from pydantic import BaseModel

class DrawingAnalysisResponse(BaseModel):
    status: str
    analysis_id: str
    child_id: int
    created_at: Any
    emotion: Dict[str, Any]
    color: Dict[str, Any]
    stroke: Dict[str, Any]
    spatial: Dict[str, Any]
    objects: Optional[Dict[str, Any]] = None