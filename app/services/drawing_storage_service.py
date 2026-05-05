from bson import ObjectId
from typing import List
import base64
from app.database.db import children_col, drawing_analyses


def get_drawings_for_parent(parent_id: str) -> List[dict]:
    if not ObjectId.is_valid(parent_id):
        return []

    parent_obj_id = ObjectId(parent_id)

    children = list(children_col.find({"parent_id": parent_obj_id}))
    if not children:
        return []

    child_map = {str(child["_id"]): child for child in children}
    child_ids = list(child_map.keys())

    drawings = list(
        drawing_analyses.find({"child_id": {"$in": child_ids}}).sort("created_at", -1)
    )

    results = []
    for drawing in drawings:
        child_id = drawing.get("child_id")
        child = child_map.get(child_id)

        results.append({
            "analysis_id": str(drawing["_id"]),
            "child_id": child_id,
            "child_name": child["name"] if child else drawing.get("child_name", "Unknown"),
            "child_username": child["username"] if child else drawing.get("child_username", "Unknown"),
            "created_at": drawing.get("created_at"),
            "note": drawing.get("note"),
            "filename": drawing.get("filename"),
            "content_type": drawing.get("content_type"),
            "source_mode": drawing.get("source_mode"),
            "emotion": drawing.get("emotion"),
            "color": drawing.get("color"),
            "stroke": drawing.get("stroke"),
            "spatial": drawing.get("spatial"),
            "objects": drawing.get("objects"),
            "llm_review": drawing.get("llm_review"),
            "description": drawing.get("description"),
            "image_base64": base64.b64encode(drawing["image_bytes"]).decode("utf-8") if drawing.get("image_bytes") else None,
        })

    return results


def get_drawings_for_child_gallery(child_id: str) -> List[dict]:
    drawings = list(
        drawing_analyses.find({"child_id": child_id}).sort("created_at", -1)
    )

    return [
        {
            "analysis_id": str(d["_id"]),
            "created_at": d.get("created_at"),
            "filename": d.get("filename"),
            "source_mode": d.get("source_mode"),
            "emotion_label": d.get("emotion", {}).get("label"),
            "image_base64": base64.b64encode(d["image_bytes"]).decode("utf-8") if d.get("image_bytes") else None,
        }
        for d in drawings
    ]