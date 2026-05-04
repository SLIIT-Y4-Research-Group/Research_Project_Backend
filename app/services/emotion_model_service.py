import os
from functools import lru_cache
from typing import Tuple

import numpy as np
from PIL import Image
import torch
import timm
from torchvision import transforms

from app.core.config import EMOTION_MODEL_PATH

IMG_SIZE = 224
EMOTION_LABELS = ["sad", "happy"]


@lru_cache(maxsize=1)
def load_emotion_model(model_path: str = EMOTION_MODEL_PATH):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Emotion model not found at: {model_path}")

    checkpoint = torch.load(model_path, map_location="cpu")

    model = timm.create_model(
        "densenet121",
        pretrained=False,
        num_classes=2
    )

    state_dict = checkpoint.get("model_state_dict", checkpoint)
    model.load_state_dict(state_dict)
    model.eval()

    class_to_idx = checkpoint.get("class_to_idx", {"sad": 0, "happy": 1})
    idx_to_class = checkpoint.get(
        "idx_to_class",
        {v: k for k, v in class_to_idx.items()}
    )

    if isinstance(list(idx_to_class.keys())[0], str):
        idx_to_class = {int(k): v for k, v in idx_to_class.items()}

    return {
        "model": model,
        "class_to_idx": class_to_idx,
        "idx_to_class": idx_to_class
    }


def _get_transform():
    return transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        ),
    ])


def predict_emotion(input_data: np.ndarray) -> Tuple[int, float]:
    loaded = load_emotion_model()
    model = loaded["model"]

    if len(input_data.shape) == 2:
        input_data = np.expand_dims(input_data, axis=-1)

    if input_data.shape[-1] == 1:
        input_data = np.concatenate([input_data] * 3, axis=-1)

    if input_data.dtype != np.uint8:
        if input_data.max() <= 1.0:
            input_data = (input_data * 255).astype(np.uint8)
        else:
            input_data = input_data.astype(np.uint8)

    image = Image.fromarray(input_data).convert("RGB")
    tensor = _get_transform()(image).unsqueeze(0)

    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1)[0]

    pred_idx = int(torch.argmax(probs).item())
    confidence = float(probs[pred_idx].item())
    return pred_idx, confidence


def predict_emotion_with_label(input_data: np.ndarray):
    loaded = load_emotion_model()
    idx_to_class = loaded["idx_to_class"]

    emotion_idx, confidence = predict_emotion(input_data)
    emotion_label = idx_to_class.get(emotion_idx, EMOTION_LABELS[emotion_idx]).lower()

    if emotion_label not in ("happy", "sad"):
        if "happy" in emotion_label:
            emotion_label = "happy"
        else:
            emotion_label = "sad"

    return emotion_idx, emotion_label, confidence