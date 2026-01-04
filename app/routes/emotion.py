# app/routes/emotion.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.emotion_model_service import predict_emotion
import numpy as np

router = APIRouter()

class EmotionRequest(BaseModel):
    data: list  # or list of numbers, or encoded image

class EmotionResponse(BaseModel):
    emotion_idx: int
    confidence: float

@router.post("/predict", response_model=EmotionResponse)
async def predict_emotion_api(request: EmotionRequest):
    input_array = np.array(request.data)
    idx, conf = predict_emotion(input_array)
    return {"emotion_idx": idx, "confidence": conf}
