# app/routes/emotion_routes.py
from fastapi import APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel
import numpy as np
import base64
import io
from PIL import Image
from app.services.emotion_model_service import predict_emotion, EMOTION_LABELS, IMG_SIZE

router = APIRouter()

class EmotionRequest(BaseModel):
    data: list  # input vector or preprocessed image array

class ImageRequest(BaseModel):
    image: str  # base64 encoded image

class EmotionResponse(BaseModel):
    emotion_idx: int
    emotion_label: str
    confidence: float

@router.post("/predict", response_model=EmotionResponse)
async def predict_emotion_api(request: EmotionRequest):
    """Predict emotion from preprocessed image array."""
    input_array = np.array(request.data)
    idx, conf = predict_emotion(input_array)
    label = EMOTION_LABELS[idx] if idx < len(EMOTION_LABELS) else "unknown"
    return {"emotion_idx": idx, "emotion_label": label, "confidence": conf}

@router.post("/predict-image", response_model=EmotionResponse)
async def predict_emotion_from_image(request: ImageRequest):
    """
    Predict emotion from a base64-encoded image.
    
    The image will be automatically resized to 224x224 and preprocessed.
    Accepts any common image format (JPEG, PNG, etc.)
    """
    try:
        # Decode base64 image
        image_data = request.image
        
        # Handle data URL format (e.g., "data:image/jpeg;base64,/9j/4AAQ...")
        if "," in image_data:
            image_data = image_data.split(",")[1]
        
        # Decode base64 to bytes
        image_bytes = base64.b64decode(image_data)
        
        # Open image with PIL
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Resize to model input size (224x224)
        image = image.resize((IMG_SIZE, IMG_SIZE))
        
        # Convert to numpy array (keep 0-255 range, preprocessing happens in service)
        img_array = np.array(image, dtype=np.float32)
        
        # Predict emotion
        idx, conf = predict_emotion(img_array)
        label = EMOTION_LABELS[idx] if idx < len(EMOTION_LABELS) else "unknown"
        
        return {"emotion_idx": idx, "emotion_label": label, "confidence": conf}
        
    except base64.binascii.Error:
        raise HTTPException(status_code=400, detail="Invalid base64 encoding")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")


@router.post("/upload", response_model=EmotionResponse)
async def predict_emotion_from_upload(file: UploadFile = File(...)):
    """
    Predict emotion from an uploaded image file.
    
    Submit as multipart/form-data with field name 'file'.
    The image will be automatically resized to 224x224 and preprocessed.
    Accepts any common image format (JPEG, PNG, etc.)
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read file contents
        contents = await file.read()
        
        # Open image with PIL
        image = Image.open(io.BytesIO(contents))
        
        # Convert to RGB if necessary
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Resize to model input size (224x224)
        image = image.resize((IMG_SIZE, IMG_SIZE))
        
        # Convert to numpy array (keep 0-255 range, preprocessing happens in service)
        img_array = np.array(image, dtype=np.float32)
        
        # Predict emotion
        idx, conf = predict_emotion(img_array)
        label = EMOTION_LABELS[idx] if idx < len(EMOTION_LABELS) else "unknown"
        
        return {"emotion_idx": idx, "emotion_label": label, "confidence": conf}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")
