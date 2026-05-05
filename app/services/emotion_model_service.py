import os
from functools import lru_cache
from typing import Tuple

import numpy as np
import os
import tempfile
import urllib.request
import shutil
import h5py
import logging
from PIL import Image
import torch
import timm
from torchvision import transforms

from app.core.config import EMOTION_MODEL_PATH

IMG_SIZE = 224

# Emotion labels
EMOTION_LABELS = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']
DEFAULT_LOCAL_MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "face_emotion_model.h5")

_HF_EMOTION_PIPELINE = None
_FACE_EMOTION_MODEL = None
_FACE_EMOTION_MODEL_LOAD_ATTEMPTED = False
_DOWNLOADED_MODEL_PATH = None
logger = logging.getLogger(__name__)

_HF_LABEL_ALIASES = {
    "angry": ["angry", "anger", "mad"],
    "disgust": ["disgust", "disgusted"],
    "fear": ["fear", "fearful", "scared"],
    "happy": ["happy", "happiness", "joy", "smile"],
    "neutral": ["neutral", "calm", "normal"],
    "sad": ["sad", "sadness", "unhappy"],
    "surprise": ["surprise", "surprised"],
}


def _get_emotion_provider():
    provider = os.getenv("EMOTION_PROVIDER", "deepface").strip().lower()
    return provider if provider in {"deepface", "huggingface"} else "deepface"


def _get_hf_emotion_pipeline():
    global _HF_EMOTION_PIPELINE
    if _HF_EMOTION_PIPELINE is not None:
        return _HF_EMOTION_PIPELINE

    from transformers import pipeline

    model_name = os.getenv("EMOTION_MODEL_NAME", "").strip()
    if not model_name:
        return None

    _HF_EMOTION_PIPELINE = pipeline("image-classification", model=model_name)
    return _HF_EMOTION_PIPELINE


def _map_hf_label_to_emotion(label):
    label_lower = label.lower()
    for target, aliases in _HF_LABEL_ALIASES.items():
        if any(alias in label_lower for alias in aliases):
            return target
    return None


def _load_model_with_compat(load_model_fn, model_path: str):
    from tensorflow.keras import mixed_precision
    custom_objects = {
        "DTypePolicy": mixed_precision.Policy,
        "Policy": mixed_precision.Policy,
    }
    return load_model_fn(model_path, compile=False, custom_objects=custom_objects)


def _predict_emotion_hf(input_data):
    pipeline_fn = _get_hf_emotion_pipeline()
    if pipeline_fn is None:
        raise RuntimeError("Hugging Face emotion model is not configured. Set EMOTION_MODEL_NAME.")

    pil_image = Image.fromarray(input_data)
    results = pipeline_fn(pil_image)
    if not isinstance(results, list):
        results = [results]

    best_label = None
    best_score = -1.0
    for item in results:
        label = item.get("label", "")
        score = float(item.get("score", 0))
        mapped = _map_hf_label_to_emotion(label)
        if mapped and score > best_score:
            best_label = mapped
            best_score = score

    if best_label is None:
        return 4, 0.5

    return EMOTION_LABELS.index(best_label), max(0.0, min(1.0, best_score))

def _get_face_emotion_model():
    global _FACE_EMOTION_MODEL, _FACE_EMOTION_MODEL_LOAD_ATTEMPTED, _DOWNLOADED_MODEL_PATH
    if _FACE_EMOTION_MODEL_LOAD_ATTEMPTED:
        return _FACE_EMOTION_MODEL

    _FACE_EMOTION_MODEL_LOAD_ATTEMPTED = True
    try:
        from tensorflow.keras.models import load_model

        is_production = os.getenv("PRODUCTION", "false").strip().lower() == "true"
        local_model_path = os.getenv("LOCAL_MODEL_PATH", DEFAULT_LOCAL_MODEL_PATH).strip() or DEFAULT_LOCAL_MODEL_PATH
        aws_model_path = os.getenv("AWS_MODEL_PATH", "").strip()

        model_source = local_model_path
        if is_production and aws_model_path:
            model_source = aws_model_path
            logger.info("PRODUCTION=true, using AWS model path: %s", aws_model_path)
        else:
            logger.info("PRODUCTION=false or AWS_MODEL_PATH empty, using local model path: %s", local_model_path)

        if model_source.startswith("http://") or model_source.startswith("https://"):
            model_filename = os.path.basename(model_source) or "face_emotion_model.h5"
            download_path = os.path.join(tempfile.gettempdir(), model_filename)
            logger.info("Downloading emotion model from URL: %s", model_source)
            urllib.request.urlretrieve(model_source, download_path)
            logger.info("Downloaded emotion model to temp path: %s", download_path)
            _DOWNLOADED_MODEL_PATH = download_path
            try:
                logger.info("Attempting to load downloaded model: %s", download_path)
                _FACE_EMOTION_MODEL = _load_model_with_compat(load_model, download_path)
                logger.info("Loaded downloaded model successfully")
            except Exception as load_err:
                if "batch_shape" not in str(load_err):
                    logger.exception("Failed loading downloaded model (non-batch_shape error)")
                    raise
                logger.warning("Detected batch_shape compatibility issue. Applying patch to downloaded model.")
                patched_path = os.path.join(tempfile.gettempdir(), f"patched_{model_filename}")
                shutil.copyfile(download_path, patched_path)
                with h5py.File(patched_path, "r+") as f:
                    if "model_config" in f.attrs:
                        cfg = f.attrs["model_config"]
                        if isinstance(cfg, bytes):
                            cfg = cfg.decode("utf-8")
                        cfg = cfg.replace('"batch_shape"', '"batch_input_shape"')
                        f.attrs["model_config"] = cfg.encode("utf-8")
                _DOWNLOADED_MODEL_PATH = patched_path
                logger.info("Attempting to load patched downloaded model: %s", patched_path)
                _FACE_EMOTION_MODEL = _load_model_with_compat(load_model, patched_path)
                logger.info("Loaded patched downloaded model successfully")
        elif os.path.exists(model_source):
            try:
                logger.info("Attempting to load local model from: %s", model_source)
                _FACE_EMOTION_MODEL = _load_model_with_compat(load_model, model_source)
                logger.info("Loaded local model successfully")
            except Exception as load_err:
                if "batch_shape" not in str(load_err):
                    logger.exception("Failed loading local model (non-batch_shape error)")
                    raise
                logger.warning("Detected batch_shape compatibility issue. Applying patch to local model.")
                patched_path = os.path.join(tempfile.gettempdir(), "patched_local_face_emotion_model.h5")
                shutil.copyfile(model_source, patched_path)
                with h5py.File(patched_path, "r+") as f:
                    if "model_config" in f.attrs:
                        cfg = f.attrs["model_config"]
                        if isinstance(cfg, bytes):
                            cfg = cfg.decode("utf-8")
                        cfg = cfg.replace('"batch_shape"', '"batch_input_shape"')
                        f.attrs["model_config"] = cfg.encode("utf-8")
                logger.info("Attempting to load patched local model from: %s", patched_path)
                _FACE_EMOTION_MODEL = _load_model_with_compat(load_model, patched_path)
                logger.info("Loaded patched local model successfully")
        else:
            logger.error("face_emotion_model.h5 not found at: %s", model_source)
    except Exception as e:
        logger.exception("Failed to load face_emotion_model.h5: %s", e)
        _FACE_EMOTION_MODEL = None
    return _FACE_EMOTION_MODEL

def _predict_emotion_local_h5(input_data):
    model = _get_face_emotion_model()
    if model is None:
        logger.warning("Local/S3 face emotion model unavailable for prediction")
        raise RuntimeError("Local face emotion model is unavailable.")

    resized = Image.fromarray(input_data).resize((IMG_SIZE, IMG_SIZE))
    arr = np.array(resized).astype(np.float32) / 255.0
    arr = np.expand_dims(arr, axis=0)

    preds = model.predict(arr, verbose=0)
    preds = np.array(preds).squeeze()
    if preds.ndim != 1 or preds.size == 0:
        raise RuntimeError("Invalid prediction shape from local model.")

    # Align to known label set size defensively
    pred_len = min(len(EMOTION_LABELS), preds.shape[0])
    scores = preds[:pred_len]
    emotion_idx = int(np.argmax(scores))
    confidence = float(scores[emotion_idx])
    confidence = max(0.0, min(1.0, confidence))
    return emotion_idx, confidence


def predict_emotion(input_data):
    """
    Predict emotion from input data using DeepFace or Hugging Face.
    Input should be an image as numpy array (H, W, 3) with values 0-255 or 0-1.
    """
    # Ensure correct input shape
    if len(input_data.shape) == 2:
        input_data = np.expand_dims(input_data, axis=-1)

    if input_data.shape[-1] == 1:
        input_data = np.concatenate([input_data] * 3, axis=-1)
    
    # Ensure uint8 format for DeepFace
    if input_data.max() <= 1.0:
        input_data = (input_data * 255).astype(np.uint8)
    else:
        input_data = input_data.astype(np.uint8)
    
    # Primary: local .h5 model
    try:
        return _predict_emotion_local_h5(input_data)
    except Exception as e:
        logger.warning("Local face_emotion_model.h5 inference error: %s", e)

    provider = _get_emotion_provider()
    if provider == "huggingface":
        try:
            return _predict_emotion_hf(input_data)
        except Exception as e:
            logger.warning("Hugging Face error: %s", e)

    try:
        result = DeepFace.analyze(
            input_data,
            actions=['emotion'],
            enforce_detection=False,
            silent=True
        )

        if isinstance(result, list):
            result = result[0]

        emotions = result.get('emotion', {})
        dominant_emotion = result.get('dominant_emotion', 'neutral')
        emotion_label = dominant_emotion.lower()

        if emotion_label in EMOTION_LABELS:
            emotion_idx = EMOTION_LABELS.index(emotion_label)
        else:
            emotion_idx = 4
            emotion_label = 'neutral'

        confidence = emotions.get(dominant_emotion, 0) / 100.0
        return emotion_idx, confidence
    except Exception as e:
        logger.warning("DeepFace error: %s", e)
        return 4, 0.5

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