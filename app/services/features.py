from typing import Dict, List, Tuple, Optional
import numpy as np
import cv2

# ---------- helpers ----------
def _safe_float(x) -> float:
    return float(x) if x is not None else 0.0

def _to_gray(bgr: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

def _ink_mask_from_hsv(bgr: np.ndarray) -> np.ndarray:
    """
    Ink mask: pixels that are not paper-white.
    Tune thresholds based on your scanning / photo pipeline.
    """
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    H, S, V = cv2.split(hsv)

    # paper: high V, low S
    ink = (V < 245) | (S > 25)
    mask = (ink.astype(np.uint8) * 255)

    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k, iterations=2)
    return mask


# ---------- Color analysis ----------
def color_analysis(bgr: np.ndarray) -> Dict:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    H, S, V = cv2.split(hsv)

    mean_v = float(np.mean(V))
    mean_s = float(np.mean(S))

    # colored pixels: not near-white and not near-gray
    colored_mask = ((V < 245) & (S > 25)).astype(np.uint8)
    colored_ratio = float(np.mean(colored_mask))

    # Hue histogram only for colored pixels
    h_vals = H[colored_mask == 1]
    hist_bins = 18
    if len(h_vals) > 0:
        hist = np.histogram(h_vals, bins=hist_bins, range=(0, 180))[0].astype(int).tolist()
        dominant_bin = int(np.argmax(hist))
        dominant_hue_center = int((dominant_bin + 0.5) * (180 / hist_bins))
    else:
        hist = [0] * hist_bins
        dominant_hue_center = None

    tags: List[str] = []
    if colored_ratio < 0.03:
        tags.append("mostly_blank")
    if mean_v < 90:
        tags.append("dark_tones")
    elif mean_v > 220:
        tags.append("very_bright")

    if mean_s > 110:
        tags.append("high_saturation")
    elif mean_s < 40:
        tags.append("low_saturation")

    if dominant_hue_center is not None and colored_ratio >= 0.03:
        h = dominant_hue_center
        if h < 15 or h >= 165:
            tags.append("dominant_red")
        elif 15 <= h < 35:
            tags.append("dominant_orange")
        elif 35 <= h < 55:
            tags.append("dominant_yellow")
        elif 55 <= h < 85:
            tags.append("dominant_green")
        elif 85 <= h < 125:
            tags.append("dominant_blue")
        else:
            tags.append("dominant_purple")

    return {
        "mean_brightness_v": mean_v,
        "mean_saturation_s": mean_s,
        "colored_ratio": colored_ratio,
        "dominant_hue_center": dominant_hue_center,
        "hue_histogram_18bins": hist,
        "tags": tags
    }


# ---------- Stroke / line features ----------
def stroke_features(bgr: np.ndarray) -> Dict:
    gray = _to_gray(bgr)

    # Edges approximate amount of strokes
    edges = cv2.Canny(gray, threshold1=50, threshold2=150)
    edge_density = float(np.mean(edges > 0))

    # Thickness proxy: dilate edges slightly
    kernel = np.ones((3, 3), np.uint8)
    dil = cv2.dilate(edges, kernel, iterations=1)
    thickness_proxy = float(np.mean(dil > 0) - np.mean(edges > 0))

    # Darkness proxy (lower mean = darker / heavier strokes overall)
    mean_intensity = float(np.mean(gray))

    # Optional: ink coverage (more stable than edges sometimes)
    ink_mask = _ink_mask_from_hsv(bgr)
    ink_ratio = float(np.mean(ink_mask > 0))

    return {
        "edge_density": edge_density,
        "thickness_proxy": thickness_proxy,
        "mean_intensity": mean_intensity,
        "ink_ratio": ink_ratio,
        "notes": [
            "edge_density ~ stroke amount / complexity",
            "thickness_proxy ~ heavier lines",
            "mean_intensity lower ~ darker overall drawing",
            "ink_ratio ~ how much of page is used by non-white pixels"
        ]
    }


# ---------- Spatial / composition features ----------
def spatial_analysis(bgr: np.ndarray) -> Dict:
    h, w = bgr.shape[:2]
    mask = _ink_mask_from_hsv(bgr)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return {
            "has_foreground": False,
            "bbox_norm": {"x": 0, "y": 0, "w": 0, "h": 0},
            "center_offset": {"dx": 0, "dy": 0},
            "coverage": 0.0,
            "quadrant_ink": {"tl": 0, "tr": 0, "bl": 0, "br": 0},
            "notes": ["no contours found (blank/very light drawing)"]
        }

    # Bounding box over ALL contours (more stable than picking only largest)
    xs, ys, x2s, y2s = [], [], [], []
    for c in contours:
        x, y, bw, bh = cv2.boundingRect(c)
        xs.append(x); ys.append(y); x2s.append(x + bw); y2s.append(y + bh)

    x1, y1, x2, y2 = min(xs), min(ys), max(x2s), max(y2s)
    bw, bh = x2 - x1, y2 - y1

    bbox_norm = {"x": x1 / w, "y": y1 / h, "w": bw / w, "h": bh / h}
    coverage = float((bw * bh) / (w * h))

    cx = (x1 + bw / 2) / w
    cy = (y1 + bh / 2) / h
    center_offset = {"dx": float(cx - 0.5), "dy": float(cy - 0.5)}

    # Quadrant ink distribution (layout balance)
    midx, midy = w // 2, h // 2
    tl = float(np.mean(mask[:midy, :midx] > 0))
    tr = float(np.mean(mask[:midy, midx:] > 0))
    bl = float(np.mean(mask[midy:, :midx] > 0))
    br = float(np.mean(mask[midy:, midx:] > 0))

    return {
        "has_foreground": True,
        "bbox_norm": {k: float(v) for k, v in bbox_norm.items()},
        "center_offset": center_offset,
        "coverage": float(coverage),
        "quadrant_ink": {"tl": tl, "tr": tr, "bl": bl, "br": br},
        "notes": [
            "coverage small => small/withdrawn; large => expansive use of page",
            "center_offset near (0,0) => centered; larger offsets => peripheral",
            "quadrant_ink indicates balance / clustering"
        ]
    }