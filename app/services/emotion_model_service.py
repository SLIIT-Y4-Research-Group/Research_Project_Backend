# app/services/emotion_model_service.py
import numpy as np
import os
from PIL import Image
import io

# Use DeepFace for emotion detection (pre-trained model)
from deepface import DeepFace

# Image size (DeepFace handles resizing internally)
IMG_SIZE = 224

# Emotion labels
EMOTION_LABELS = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']

def predict_emotion(input_data):
    """
    Predict emotion from input data using DeepFace.
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
    return emotion_idx, emotion_label, confidence
