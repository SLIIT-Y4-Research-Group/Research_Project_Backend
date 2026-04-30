import cv2
import numpy as np
from typing import Dict

def color_features(bgr: np.ndarray) -> Dict:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    H, S, V = cv2.split(hsv)

    mean_v = float(np.mean(V))
    mean_s = float(np.mean(S))

    # Consider "colored pixels" as those not near-white and not near-gray
    colored_mask = ((V < 245) & (S > 25)).astype(np.uint8)

    colored_ratio = float(np.mean(colored_mask))  # 0..1

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

    tags = []

    # Blank / paper-heavy
    if colored_ratio < 0.03:
        tags.append("mostly_blank")

    # Dark / light
    if mean_v < 90:
        tags.append("dark_tones")
    elif mean_v > 220:
        tags.append("very_bright")

    # Saturation
    if mean_s > 110:
        tags.append("high_saturation")
    elif mean_s < 40:
        tags.append("low_saturation")

    # Dominant hue family (only if enough colored pixels)
    if dominant_hue_center is not None and colored_ratio >= 0.03:
        # Hue ranges in OpenCV: 0-180
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