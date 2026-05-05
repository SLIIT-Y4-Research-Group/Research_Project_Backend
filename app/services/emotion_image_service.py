import base64
import io
from typing import Tuple

import numpy as np
from PIL import Image

from app.services.emotion_model_service import EMOTION_LABELS, IMG_SIZE, predict_emotion


def _decode_base64_to_pil(image_b64: str) -> Image.Image:
    image_data = image_b64
    if "," in image_data:
        image_data = image_data.split(",", 1)[1]
    image_bytes = base64.b64decode(image_data)
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode != "RGB":
        image = image.convert("RGB")
    return image


def predict_emotion_from_base64(image_b64: str) -> Tuple[int, str, float]:
    image = _decode_base64_to_pil(image_b64)
    image_resized = image.resize((IMG_SIZE, IMG_SIZE))
    img_array = np.array(image_resized, dtype=np.float32)
    idx, conf = predict_emotion(img_array)
    label = EMOTION_LABELS[idx] if idx < len(EMOTION_LABELS) else "unknown"
    return idx, label, conf

