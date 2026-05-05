# app/services/emotion_model_service.py
import numpy as np
import os
from PIL import Image

# Use DeepFace or Hugging Face for emotion detection (pre-trained models)
from deepface import DeepFace

# Image size (DeepFace handles resizing internally)
IMG_SIZE = 224

# Emotion labels
EMOTION_LABELS = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "face_emotion_model.h5")

_HF_EMOTION_PIPELINE = None
_FACE_EMOTION_MODEL = None
_FACE_EMOTION_MODEL_LOAD_ATTEMPTED = False

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
    global _FACE_EMOTION_MODEL, _FACE_EMOTION_MODEL_LOAD_ATTEMPTED
    if _FACE_EMOTION_MODEL_LOAD_ATTEMPTED:
        return _FACE_EMOTION_MODEL

    _FACE_EMOTION_MODEL_LOAD_ATTEMPTED = True
    try:
        from tensorflow.keras.models import load_model
        if os.path.exists(MODEL_PATH):
            _FACE_EMOTION_MODEL = load_model(MODEL_PATH, compile=False)
        else:
            print(f"face_emotion_model.h5 not found at: {MODEL_PATH}")
    except Exception as e:
        print(f"Failed to load face_emotion_model.h5: {e}")
        _FACE_EMOTION_MODEL = None
    return _FACE_EMOTION_MODEL

def _predict_emotion_local_h5(input_data):
    model = _get_face_emotion_model()
    if model is None:
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
        # If 2D (H, W), add channel dimension
        input_data = np.expand_dims(input_data, axis=-1)
    
    if input_data.shape[-1] == 1:
        # If grayscale, convert to RGB
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
        print(f"Local face_emotion_model.h5 inference error: {e}")

    provider = _get_emotion_provider()
    if provider == "huggingface":
        try:
            return _predict_emotion_hf(input_data)
        except Exception as e:
            print(f"Hugging Face error: {e}")
            # Continue fallback to DeepFace

    try:
        # Use DeepFace to analyze emotion
        result = DeepFace.analyze(
            input_data,
            actions=['emotion'],
            enforce_detection=False,  # Don't fail if face not detected
            silent=True
        )

        # Handle list result (multiple faces) - take first face
        if isinstance(result, list):
            result = result[0]

        # Get emotion predictions
        emotions = result.get('emotion', {})
        dominant_emotion = result.get('dominant_emotion', 'neutral')

        # Map to our label format
        emotion_label = dominant_emotion.lower()
        if emotion_label in EMOTION_LABELS:
            emotion_idx = EMOTION_LABELS.index(emotion_label)
        else:
            emotion_idx = 4  # default to neutral
            emotion_label = 'neutral'

        # Get confidence (DeepFace returns percentages)
        confidence = emotions.get(dominant_emotion, 0) / 100.0

        return emotion_idx, confidence

    except Exception as e:
        print(f"DeepFace error: {e}")
        # Fallback to neutral
        return 4, 0.5

def predict_emotion_with_label(input_data):
    """Predict emotion and return both index and label."""
    emotion_idx, confidence = predict_emotion(input_data)
    emotion_label = EMOTION_LABELS[emotion_idx] if emotion_idx < len(EMOTION_LABELS) else "unknown"
    return emotion_idx, emotion_label, confidence
