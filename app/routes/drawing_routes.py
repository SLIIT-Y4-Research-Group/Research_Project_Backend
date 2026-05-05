from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from datetime import datetime
from PIL import Image
import io
import numpy as np
from bson import ObjectId
from fastapi import Response
from app.database.db import drawing_analyses, children_col, parents_col
from app.schemas.auth_schema import TokenData
from app.services.auth_service import get_current_child, get_current_parent
from app.services.analysis_service import (
    pil_to_bgr,
    detect_source_mode,
    color_analysis,
    stroke_features,
    spatial_arrangement,
)
from app.services.preprocess import preprocess_for_analysis
from app.services.gemini_drawing_review_service import (
    review_drawing_analysis_with_gemini_image,
)
from app.services.report_translation_service import generate_full_sinhala_report
from app.services.email_service import send_email
from app.services.drawing_storage_service import (
    get_drawings_for_parent,
    get_drawings_for_child_gallery,
)

router = APIRouter(prefix="/drawing", tags=["Drawing Analysis"])


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


def send_sad_drawing_email(parent_email: str, child_name: str, description: str) -> bool:
    subject = f"Drawing Alert for {child_name}"
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <h2>Drawing Emotion Alert</h2>
        <p>A drawing submitted by <strong>{child_name}</strong> was interpreted as <strong>sad</strong>.</p>
        <p><strong>Report:</strong></p>
        <div style="background:#f7f7f7; padding:16px; border-radius:8px; white-space:pre-wrap;">
          {description}
        </div>
        <p>This is an observations-based alert and not a medical diagnosis.</p>
      </body>
    </html>
    """
    return send_email(parent_email, subject, html_body)


@router.post("/analyze")
async def analyze_drawing(
    child_id: str = Form(...),
    note: str | None = Form(None),
    source_override: str | None = Form(None),   # "drawing_board" when sent from Flutter board
    image: UploadFile = File(...),
):
    """
    Analyze a child's drawing.

    - source_override="drawing_board"  → skip CV pipeline, go direct to Gemini
    - otherwise                        → full CV pipeline + Gemini
    """
    try:
        allowed_types = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
        if image.content_type and image.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image type: {image.content_type}",
            )

        raw = await image.read()
        try:
            pil_img = Image.open(io.BytesIO(raw)).convert("RGB")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image file")

        if not ObjectId.is_valid(child_id):
            raise HTTPException(status_code=400, detail="Invalid child ID")

        child = children_col.find_one({"_id": ObjectId(child_id)})
        if not child:
            raise HTTPException(status_code=404, detail="Child not found")

        parent = (
            parents_col.find_one({"_id": child["parent_id"]})
            if child.get("parent_id")
            else None
        )
        parent_email = parent.get("email") if parent else None

        # ── Determine pipeline mode ──────────────────────────────────────────
        is_drawing_board = source_override == "drawing_board"

        if is_drawing_board:
            # Skip all CV analysis — send directly to Gemini
            source_mode = "drawing_board"
            color = {}
            stroke = {}
            spatial = {}
            preprocess_meta = {}
        else:
            # Full CV pipeline for scanned / uploaded photos
            bgr_raw = pil_to_bgr(pil_img)
            source_mode = detect_source_mode(bgr_raw, filename=image.filename)
            bgr_proc, preprocess_meta = preprocess_for_analysis(
                bgr_raw,
                source_mode=source_mode,
            )
            color = color_analysis(bgr_proc, source_mode=source_mode)
            stroke = stroke_features(bgr_proc, source_mode=source_mode)
            spatial = spatial_arrangement(bgr_proc, source_mode=source_mode)

        # ── Build LLM input ──────────────────────────────────────────────────
        llm_input = {
            "source_mode": source_mode,
            "note": note,
            "color": color,
            "stroke": stroke,
            "spatial": spatial,
            "preprocess": preprocess_meta,
            "filename": image.filename,
            "child_age": child.get("age"),
            "child_name": child.get("name"),
            "child_username": child.get("username"),
        }

        # ── Gemini review ────────────────────────────────────────────────────
        llm_review = review_drawing_analysis_with_gemini_image(
            image_bytes=raw,
            mime_type=image.content_type or "image/jpeg",
            analysis_payload=llm_input,
            source_mode=source_mode,          # NEW — passes routing hint
        )

        # ── Sinhala full report ──────────────────────────────────────────────
        sinhala_report = generate_full_sinhala_report(llm_review)

        emotion = {
            "label": llm_review.get("final_emotion", "sad"),
            "confidence": llm_review.get("confidence_level", "medium"),
        }

        # ── Persist to MongoDB ───────────────────────────────────────────────
        doc = {
            "child_id": child_id,
            "parent_id": str(child["parent_id"]) if child.get("parent_id") else None,
            "parent_email": parent_email,
            "child_name": child.get("name"),
            "child_username": child.get("username"),
            "note": note,
            "created_at": datetime.utcnow(),
            "source_mode": source_mode,
            "emotion": emotion,
            # CV fields — empty dicts for drawing_board submissions
            "color": color,
            "stroke": stroke,
            "spatial": spatial,
            # LLM-derived structured fields (rich JSON)
            "objects": llm_review.get("detected_objects", []),
            "missed_objects": llm_review.get("missed_objects", []),
            "color_analysis": llm_review.get("color_analysis", {}),
            "spatial_analysis": llm_review.get("spatial_analysis", {}),
            "stroke_analysis": llm_review.get("stroke_analysis", {}),
            "developmental_notes": llm_review.get("developmental_notes", {}),
            "parent_guidance": llm_review.get("parent_guidance", {}),
            "llm_review": llm_review,
            "description": llm_review.get("description", ""),
            "description_en": llm_review.get("description", ""),
            "description_si": sinhala_report,
            "emotional_condition": llm_review.get("emotional_condition", ""),
            "emotional_condition_en": llm_review.get("emotional_condition", ""),
            "filename": image.filename,
            "content_type": image.content_type,
            "image_bytes": raw,
        }

        doc = to_python_types(doc)
        result = drawing_analyses.insert_one(doc)

        # ── Alert email ──────────────────────────────────────────────────────
        if emotion["label"] == "sad" and parent_email:
            send_sad_drawing_email(
                parent_email=parent_email,
                child_name=child.get("name", "Child"),
                description=doc.get("description_en", "No description available."),
            )

        return {
            "status": "success",
            "analysis_id": str(result.inserted_id),
            "child_id": child_id,
            "created_at": doc["created_at"],
            "source_mode": source_mode,
            "emotion": emotion,
            "color": color,
            "stroke": stroke,
            "spatial": spatial,
            "objects": doc["objects"],
            "missed_objects": doc["missed_objects"],
            "color_analysis": doc["color_analysis"],
            "spatial_analysis": doc["spatial_analysis"],
            "stroke_analysis": doc["stroke_analysis"],
            "developmental_notes": doc["developmental_notes"],
            "parent_guidance": doc["parent_guidance"],
            "llm_review": llm_review,
            "description": doc.get("description_en"),
            "description_si": doc.get("description_si"),
            "emotional_condition_en": doc.get("emotional_condition_en"),
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Drawing analysis failed: {repr(e)}")


@router.get("/image/{analysis_id}")
def get_drawing_image(analysis_id: str):
    if not ObjectId.is_valid(analysis_id):
        raise HTTPException(status_code=400, detail="Invalid analysis ID")

    drawing = drawing_analyses.find_one({"_id": ObjectId(analysis_id)})
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")

    image_bytes = drawing.get("image_bytes")
    if not image_bytes:
        raise HTTPException(status_code=404, detail="Image not found")

    content_type = drawing.get("content_type") or "image/jpeg"
    return Response(content=bytes(image_bytes), media_type=content_type)


@router.get("/parent/me")
def list_parent_drawings(current_parent: TokenData = Depends(get_current_parent)):
    try:
        drawings = get_drawings_for_parent(current_parent.id)
        return {"status": "success", "items": drawings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch drawings: {str(e)}")


@router.get("/child/me/gallery")
def child_gallery(current_child: TokenData = Depends(get_current_child)):
    try:
        drawings = get_drawings_for_child_gallery(current_child.id)
        return {"status": "success", "items": drawings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch child gallery: {str(e)}")