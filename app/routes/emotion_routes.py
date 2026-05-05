# app/routes/emotion_routes.py
from fastapi import APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel
from typing import Optional
import numpy as np
import base64
import io
from PIL import Image
from app.services.emotion_model_service import predict_emotion, EMOTION_LABELS, IMG_SIZE
from app.services.face_generation_service import generate_happy_face
from app.services.emotion_image_service import predict_emotion_from_base64

router = APIRouter(prefix="/emotion", tags=["Emotion"])

class EmotionRequest(BaseModel):
    data: list  # input vector or preprocessed image array

class ImageRequest(BaseModel):
    image: str  # base64 encoded image

class EmotionResponse(BaseModel):
    emotion_idx: int
    emotion_label: str
    confidence: float

class EmotionWithHappyFaceResponse(BaseModel):
    emotion_idx: int
    emotion_label: str
    confidence: float
    is_happy: bool
    happy_face_image: Optional[str] = None  # base64 encoded image
    message: Optional[str] = None

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
        idx, label, conf = predict_emotion_from_base64(request.image)
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


@router.post("/predict-with-happy-face", response_model=EmotionWithHappyFaceResponse)
async def predict_emotion_and_generate_happy(request: ImageRequest):
    """
    Predict emotion from a base64-encoded image.
    If the person is not happy, generate a happy version of their face.
    
    Returns:
    - Original emotion detection results
    - If not happy: a base64-encoded image of the person with a happy expression
    """
    try:
        # Decode base64 image
        image_data = request.image
        
        # Handle data URL format
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
        image_resized = image.resize((IMG_SIZE, IMG_SIZE))
        
        # Convert to numpy array
        img_array = np.array(image_resized, dtype=np.float32)
        
        # Predict emotion
        idx, conf = predict_emotion(img_array)
        label = EMOTION_LABELS[idx] if idx < len(EMOTION_LABELS) else "unknown"
        
        # Check if person is happy
        is_happy = label.lower() == 'happy'
        
        response_data = {
            "emotion_idx": idx,
            "emotion_label": label,
            "confidence": conf,
            "is_happy": is_happy,
        }
        
        # If not happy, generate happy version
        if not is_happy:
            # Use original size image for better quality generation
            original_array = np.array(image, dtype=np.uint8)
            
            # Generate happy face
            happy_image_base64, success = generate_happy_face(original_array)
            
            if success and happy_image_base64:
                response_data["happy_face_image"] = happy_image_base64
                response_data["message"] = f"We detected you're feeling {label}. Here's a happier version of you to brighten your day!"
            else:
                response_data["message"] = f"We detected you're feeling {label}, but couldn't generate a happy version. Keep smiling!"
        else:
            response_data["message"] = "You're already happy! Keep that beautiful smile!"
        
        return response_data
        
    except base64.binascii.Error:
        raise HTTPException(status_code=400, detail="Invalid base64 encoding")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")


@router.post("/upload-with-happy-face", response_model=EmotionWithHappyFaceResponse)
async def predict_emotion_and_generate_happy_upload(file: UploadFile = File(...)):
    """
    Predict emotion from an uploaded image file.
    If the person is not happy, generate a happy version of their face.
    
    Submit as multipart/form-data with field name 'file'.
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
        
        # Resize to model input size for prediction
        image_resized = image.resize((IMG_SIZE, IMG_SIZE))
        
        # Convert to numpy array
        img_array = np.array(image_resized, dtype=np.float32)
        
        # Predict emotion
        idx, conf = predict_emotion(img_array)
        label = EMOTION_LABELS[idx] if idx < len(EMOTION_LABELS) else "unknown"
        
        # Check if person is happy
        is_happy = label.lower() == 'happy'
        
        response_data = {
            "emotion_idx": idx,
            "emotion_label": label,
            "confidence": conf,
            "is_happy": is_happy,
        }
        
        # If not happy, generate happy version
        if not is_happy:
            # Use original size image for better quality
            original_array = np.array(image, dtype=np.uint8)
            
            # Generate happy face
            happy_image_base64, success = generate_happy_face(original_array)
            
            if success and happy_image_base64:
                response_data["happy_face_image"] = happy_image_base64
                response_data["message"] = f"We detected you're feeling {label}. Here's a happier version of you to brighten your day!"
            else:
                response_data["message"] = f"We detected you're feeling {label}, but couldn't generate a happy version. Keep smiling!"
        else:
            response_data["message"] = "You're already happy! Keep that beautiful smile!"
        
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")
