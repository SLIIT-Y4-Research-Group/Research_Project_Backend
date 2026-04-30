import cv2
import numpy as np
from typing import Dict

def spatial_features(bgr: np.ndarray) -> Dict:
    h, w = bgr.shape[:2]

    # 1) Build "ink mask" = NOT white-ish pixels
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    H, S, V = cv2.split(hsv)

    # White paper tends to have: high V, low S
    ink = (V < 245) | (S > 25)  # tune if needed
    mask = (ink.astype(np.uint8) * 255)

    # 2) Remove tiny noise
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k, iterations=2)

    # 3) Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return {
            "has_foreground": False,
            "bbox_norm": {"x": 0, "y": 0, "w": 0, "h": 0},
            "center_offset": {"dx": 0, "dy": 0},
            "coverage": 0.0,
            "notes": ["no contours found (likely blank/very light drawing)"]
        }

    # 4) Filter out contours touching border (frame/scanner edges)
    def touches_border(x, y, bw, bh, margin=3):
        return x <= margin or y <= margin or (x + bw) >= (w - margin) or (y + bh) >= (h - margin)

    candidates = []
    for c in contours:
        x, y, bw, bh = cv2.boundingRect(c)
        area = bw * bh
        if area < 0.01 * (w * h):  # ignore tiny specks
            continue
        if touches_border(x, y, bw, bh):
            continue
        candidates.append((area, x, y, bw, bh))

    # If everything touches border, fallback to largest contour anyway
    if not candidates:
        c = max(contours, key=cv2.contourArea)
        x, y, bw, bh = cv2.boundingRect(c)
    else:
        _, x, y, bw, bh = max(candidates, key=lambda t: t[0])

    # 5) Normalize bbox + compute composition features
    x_n, y_n = x / w, y / h
    w_n, h_n = bw / w, bh / h
    coverage = float((bw * bh) / (w * h))

    cx = (x + bw / 2) / w
    cy = (y + bh / 2) / h
    center_offset = {"dx": float(cx - 0.5), "dy": float(cy - 0.5)}

    return {
        "has_foreground": True,
        "bbox_norm": {"x": float(x_n), "y": float(y_n), "w": float(w_n), "h": float(h_n)},
        "center_offset": center_offset,
        "coverage": float(coverage),
        "notes": [
            "coverage small => small/withdrawn drawing; large => expansive/bold",
            "center_offset near (0,0) => centered; larger offsets => peripheral placement"
        ]
    }