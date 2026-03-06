from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from datetime import datetime
from PIL import Image
import io
import cv2

from app.core.config import EMOTION_MODEL_PATH, ENABLE_OBJECT_DETECTION
from app.database.db import drawing_analyses
from app.schemas.drawing_schema import DrawingAnalysisResponse

from app.services.emotion_model import load_emotion_model, predict_emotion
from app.services.analysis_service import pil_to_bgr, color_analysis, stroke_features, spatial_arrangement
from app.services.preprocess import preprocess_for_analysis

# Optional detector
detector = None
if ENABLE_OBJECT_DETECTION:
    from app.services.object_detection import load_detector, detect_objects
    detector = load_detector()

router = APIRouter(prefix="/drawing", tags=["Drawing Analysis"])

emotion_model = load_emotion_model(EMOTION_MODEL_PATH)

@router.post("/analyze", response_model=DrawingAnalysisResponse)
async def analyze_drawing(
    child_id: int = Form(...),
    note: str | None = Form(None),
    image: UploadFile = File(...)
):
    if image.content_type not in {"image/jpeg", "image/png", "image/webp", "image/jpg"}:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    raw = await image.read()
    try:
        pil_img = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Convert to BGR
    bgr_raw = pil_to_bgr(pil_img)

    # ✅ Preprocess (scan + phone camera)
    bgr_proc, preprocess_meta = preprocess_for_analysis(bgr_raw)

    # ✅ Run your CV analysis on processed image
    color = color_analysis(bgr_proc)
    stroke = stroke_features(bgr_proc)
    spatial = spatial_arrangement(bgr_proc)

    # Emotion model can stay on the original pil_img (fine)
    emotion = predict_emotion(emotion_model, pil_img)

    # ✅ Object detection (optional)
    objects = None
    if detector is not None:
        # Run on processed image to reduce background clutter
        rgb_proc = cv2.cvtColor(bgr_proc, cv2.COLOR_BGR2RGB)
        pil_proc = Image.fromarray(rgb_proc)
        objects = detect_objects(detector, pil_proc, score_thresh=0.60)

    doc = {
        "child_id": child_id,
        "note": note,
        "created_at": datetime.utcnow(),
        "emotion": emotion,
        "color": color,
        "stroke": stroke,
        "spatial": spatial,
        "objects": objects,
        "preprocess": preprocess_meta,  # ✅ store debugging meta
        "filename": image.filename,
        "content_type": image.content_type,
    }

    result = drawing_analyses.insert_one(doc)
    doc_id = str(result.inserted_id)

    # If your response_model doesn't include preprocess, don't return it.
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