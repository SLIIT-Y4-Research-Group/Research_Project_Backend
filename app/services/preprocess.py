# app/services/preprocess.py

import cv2
import numpy as np
from typing import Tuple, Dict, Any


def detect_and_crop_paper(bgr: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Detect paper area and crop it (for phone camera photos)."""

    h, w = bgr.shape[:2]
    meta = {"paper_found": False}

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)

    edges = cv2.Canny(blur, 50, 150)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return bgr, meta

    c = max(contours, key=cv2.contourArea)

    x, y, bw, bh = cv2.boundingRect(c)

    cropped = bgr[y:y+bh, x:x+bw]

    meta["paper_found"] = True
    meta["bbox"] = {"x": x, "y": y, "w": bw, "h": bh}

    return cropped, meta


def normalize_lighting(bgr: np.ndarray) -> np.ndarray:
    """Improve brightness consistency (important for phone photos)."""

    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l,a,b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    l2 = clahe.apply(l)

    merged = cv2.merge([l2,a,b])
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)


def preprocess_for_analysis(bgr: np.ndarray) -> Tuple[np.ndarray, Dict[str,Any]]:
    """Main preprocessing pipeline."""

    cropped, meta = detect_and_crop_paper(bgr)

    normalized = normalize_lighting(cropped)

    return normalized, meta