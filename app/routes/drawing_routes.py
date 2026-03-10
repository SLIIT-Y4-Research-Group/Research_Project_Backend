from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from datetime import datetime
from PIL import Image
import io
import cv2
import numpy as np

from app.core.config import (
    EMOTION_MODEL_PATH,
    ENABLE_OBJECT_DETECTION,
    YOLO_MODEL_PATH,
)
from app.database.db import drawing_analyses
from app.schemas.drawing_schema import DrawingAnalysisResponse

from app.services.emotion_model import load_emotion_model, predict_emotion
from app.services.analysis_service import (
    pil_to_bgr,
    detect_source_mode,
    color_analysis,
    stroke_features,
    spatial_arrangement,
)
from app.services.preprocess import preprocess_for_analysis

detector = None
if ENABLE_OBJECT_DETECTION:
    from app.services.object_detection import load_detector, detect_objects
    detector = load_detector(YOLO_MODEL_PATH)

router = APIRouter(prefix="/drawing", tags=["Drawing Analysis"])
emotion_model = load_emotion_model(EMOTION_MODEL_PATH)

def to_python_types(obj):
    if isinstance(obj, dict):
        return {k: to_python_types(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_python_types(v) for v in obj]
    if isinstance(obj, tuple):
        return [to_python_types(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

@router.post("/analyze", response_model=DrawingAnalysisResponse)
async def analyze_drawing(
    child_id: str = Form(...),
    note: str | None = Form(None),
    image: UploadFile = File(...)
):
    print("Received content type:", image.content_type)

    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
    if image.content_type and image.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {image.content_type}"
        )

    raw = await image.read()
    try:
        pil_img = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    bgr_raw = pil_to_bgr(pil_img)

    source_mode = detect_source_mode(bgr_raw, filename=image.filename)
    bgr_proc, preprocess_meta = preprocess_for_analysis(bgr_raw, source_mode=source_mode)

    color = color_analysis(bgr_proc, source_mode=source_mode)
    stroke = stroke_features(bgr_proc, source_mode=source_mode)
    spatial = spatial_arrangement(bgr_proc, source_mode=source_mode)

    emotion = predict_emotion(emotion_model, pil_img)

    objects = None
    if detector is not None:
        rgb_proc = cv2.cvtColor(bgr_proc, cv2.COLOR_BGR2RGB)
        pil_proc = Image.fromarray(rgb_proc)
        objects = detect_objects(detector, pil_proc, score_thresh=0.20)

    doc = {
        "child_id": child_id,
        "note": note,
        "created_at": datetime.utcnow(),
        "source_mode": source_mode,
        "emotion": emotion,
        "color": color,
        "stroke": stroke,
        "spatial": spatial,
        "objects": objects,
        "preprocess": preprocess_meta,
        "filename": image.filename,
        "content_type": image.content_type,
    }

    doc = to_python_types(doc)

    try:
        print("About to insert into MongoDB...")
        result = drawing_analyses.insert_one(doc)
        print("Inserted successfully:", result.inserted_id)
    except Exception as e:
        print("Mongo insert failed:", str(e))
        raise HTTPException(status_code=500, detail=f"Mongo insert failed: {str(e)}")

    doc_id = str(result.inserted_id)

    return {
        "status": "success",
        "analysis_id": doc_id,
        "child_id": child_id,
        "created_at": doc["created_at"],
        "emotion": emotion,
        "color": color,
        "stroke": stroke,
        "spatial": spatial,
        "objects": objects
    }