# app/services/face_generation_service.py
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import cv2
from deepface import DeepFace
import io
import base64
import os

_HF_FACE_DETECTOR = None


def _get_face_detector_provider():
    provider = os.getenv("FACE_DETECTOR_PROVIDER", "deepface").strip().lower()
    return provider if provider in {"deepface", "huggingface"} else "deepface"


def _get_hf_face_detector():
    global _HF_FACE_DETECTOR
    if _HF_FACE_DETECTOR is not None:
        return _HF_FACE_DETECTOR

    from transformers import pipeline

    model_name = os.getenv("FACE_DETECTOR_MODEL", "").strip()
    if not model_name:
        return None

    _HF_FACE_DETECTOR = pipeline("object-detection", model=model_name)
    return _HF_FACE_DETECTOR


def _get_hf_face_labels():
    labels = os.getenv("FACE_DETECTOR_LABELS", "face,person")
    return {label.strip().lower() for label in labels.split(",") if label.strip()}


def _detect_face_hf(image_array):
    detector = _get_hf_face_detector()
    if detector is None:
        raise RuntimeError("Hugging Face face detector is not configured. Set FACE_DETECTOR_MODEL.")

    pil_image = Image.fromarray(image_array)
    results = detector(pil_image)
    if not isinstance(results, list):
        results = [results]

    allowed_labels = _get_hf_face_labels()
    best = None
    best_score = -1.0
    for item in results:
        label = str(item.get("label", "")).lower()
        score = float(item.get("score", 0))
        if label in allowed_labels and score > best_score:
            best = item
            best_score = score

    if best is None:
        return None

    h, w = image_array.shape[:2]
    box = best.get("box", {})
    xmin = max(0, min(w - 1, int(box.get("xmin", 0))))
    ymin = max(0, min(h - 1, int(box.get("ymin", 0))))
    xmax = max(0, min(w, int(box.get("xmax", 0))))
    ymax = max(0, min(h, int(box.get("ymax", 0))))

    width = max(1, xmax - xmin)
    height = max(1, ymax - ymin)

    return {"x": xmin, "y": ymin, "w": width, "h": height}

def generate_happy_face(image_array):
    """
    Generate a happy version of the face in the image.
    Uses facial landmark manipulation and enhancement techniques.
    
    Args:
        image_array: numpy array of the image (H, W, 3) with values 0-255
        
    Returns:
        tuple: (happy_image_base64, success)
    """
    try:
        # Ensure uint8 format
        if image_array.max() <= 1.0:
            image_array = (image_array * 255).astype(np.uint8)
        else:
            image_array = image_array.astype(np.uint8)

        provider = _get_face_detector_provider()

        # Detect face and get facial area
        try:
            if provider == "huggingface":
                facial_area = _detect_face_hf(image_array)
                if facial_area is None:
                    return enhance_for_happiness(image_array)
            else:
                face_objs = DeepFace.extract_faces(
                    img_path=image_array,
                    enforce_detection=False,
                    detector_backend='opencv',
                    align=True
                )

                if not face_objs:
                    # If no face detected, return enhanced version
                    return enhance_for_happiness(image_array)

                # Get the first detected face
                face_obj = face_objs[0]
                facial_area = face_obj['facial_area']

            # Extract face coordinates
            x, y, w, h = facial_area['x'], facial_area['y'], facial_area['w'], facial_area['h']

            # Apply happiness transformation
            happy_image = apply_happiness_transform(image_array.copy(), x, y, w, h)

            # Convert to base64
            happy_base64 = numpy_to_base64(happy_image)

            return happy_base64, True

        except Exception as e:
            print(f"Face detection error: {e}")
            if provider == "huggingface":
                try:
                    face_objs = DeepFace.extract_faces(
                        img_path=image_array,
                        enforce_detection=False,
                        detector_backend='opencv',
                        align=True
                    )
                    if face_objs:
                        face_obj = face_objs[0]
                        facial_area = face_obj['facial_area']
                        x, y, w, h = facial_area['x'], facial_area['y'], facial_area['w'], facial_area['h']
                        happy_image = apply_happiness_transform(image_array.copy(), x, y, w, h)
                        happy_base64 = numpy_to_base64(happy_image)
                        return happy_base64, True
                except Exception as deepface_error:
                    print(f"DeepFace fallback error: {deepface_error}")
            # Fallback to simple enhancement
            return enhance_for_happiness(image_array)

    except Exception as e:
        print(f"Error generating happy face: {e}")
        return None, False


def apply_happiness_transform(image, x, y, w, h):
    """
    Apply transformations to make the face appear happier.
    Uses image processing techniques to simulate a smile.
    """
    # Convert to PIL Image for easier manipulation
    pil_image = Image.fromarray(image)
    
    # Extract face region
    face_region = pil_image.crop((x, y, x + w, y + h))
    
    # Enhance brightness slightly (happier faces often appear brighter)
    enhancer = ImageEnhance.Brightness(face_region)
    face_region = enhancer.enhance(1.15)
    
    # Enhance contrast slightly
    enhancer = ImageEnhance.Contrast(face_region)
    face_region = enhancer.enhance(1.1)
    
    # Enhance color saturation (warmer tones)
    enhancer = ImageEnhance.Color(face_region)
    face_region = enhancer.enhance(1.2)
    
    # Apply slight blur and sharpen for smoothing
    face_region = face_region.filter(ImageFilter.SMOOTH_MORE)
    
    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(face_region)
    face_region = enhancer.enhance(1.3)
    
    # Apply smile simulation using facial manipulation
    face_array = np.array(face_region)
    face_array = simulate_smile(face_array)
    face_region = Image.fromarray(face_array)
    
    # Paste the modified face back
    pil_image.paste(face_region, (x, y))
    
    # Convert back to numpy array
    return np.array(pil_image)


def simulate_smile(face_array):
    """
    Simulate a smile by manipulating the lower half of the face.
    Uses image warping techniques.
    """
    h, w = face_array.shape[:2]
    
    # Create a copy
    result = face_array.copy()
    
    # Define the region of mouth (approximately lower third of face)
    mouth_region_start = int(h * 0.6)
    mouth_region_end = int(h * 0.85)
    
    # Apply slight upward curve to mouth region
    for y in range(mouth_region_start, mouth_region_end):
        # Calculate the amount of lift (parabolic curve)
        progress = (y - mouth_region_start) / (mouth_region_end - mouth_region_start)
        lift = int(3 * progress * (1 - progress) * 4)  # Parabolic curve, max lift ~3 pixels
        
        if lift > 0 and y + lift < h:
            # Shift pixels upward to create smile effect
            center_start = int(w * 0.3)
            center_end = int(w * 0.7)
            result[y, center_start:center_end] = face_array[y + lift, center_start:center_end]
    
    # Brighten the mouth/smile area slightly
    mouth_mask = np.zeros_like(result)
    cv2.ellipse(
        mouth_mask,
        (w // 2, int(h * 0.75)),  # center
        (int(w * 0.25), int(h * 0.08)),  # axes
        0, 0, 360,  # angle and arc
        (20, 20, 20),  # color (brightness increase)
        -1  # filled
    )
    
    # Apply the brightening
    result = cv2.add(result, mouth_mask)
    
    # Add slight cheek lift (smile lines)
    result = add_smile_lines(result)
    
    return result


def add_smile_lines(face_array):
    """
    Add subtle smile lines/cheek lift to enhance the happy appearance.
    """
    h, w = face_array.shape[:2]
    result = face_array.copy()
    
    # Create subtle highlights on cheeks
    left_cheek_center = (int(w * 0.25), int(h * 0.55))
    right_cheek_center = (int(w * 0.75), int(h * 0.55))
    
    # Add soft circular highlights
    mask = np.zeros_like(result)
    cv2.circle(mask, left_cheek_center, int(w * 0.12), (15, 10, 10), -1)
    cv2.circle(mask, right_cheek_center, int(w * 0.12), (15, 10, 10), -1)
    
    # Blur the mask for soft effect
    mask = cv2.GaussianBlur(mask, (21, 21), 0)
    
    # Apply the highlights
    result = cv2.add(result, mask)
    
    return result


def enhance_for_happiness(image_array):
    """
    Fallback function when face detection fails.
    Applies general enhancements to make the image appear more positive.
    """
    try:
        pil_image = Image.fromarray(image_array)
        
        # Enhance brightness
        enhancer = ImageEnhance.Brightness(pil_image)
        pil_image = enhancer.enhance(1.2)
        
        # Enhance color
        enhancer = ImageEnhance.Color(pil_image)
        pil_image = enhancer.enhance(1.15)
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(1.1)
        
        # Convert to numpy and apply warm filter
        image_array = np.array(pil_image)
        
        # Add warm tone overlay
        warm_overlay = np.zeros_like(image_array)
        warm_overlay[:, :] = [10, 8, 0]  # Slight warm tint
        image_array = cv2.add(image_array, warm_overlay)
        
        # Convert to base64
        happy_base64 = numpy_to_base64(image_array)
        
        return happy_base64, True
        
    except Exception as e:
        print(f"Enhancement error: {e}")
        return None, False


def numpy_to_base64(image_array):
    """
    Convert numpy array to base64 encoded string.
    """
    # Convert to PIL Image
    pil_image = Image.fromarray(image_array)
    
    # Save to bytes buffer
    buffer = io.BytesIO()
    pil_image.save(buffer, format='JPEG', quality=95)
    buffer.seek(0)
    
    # Encode to base64
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    
    return image_base64


def create_comparison_image(original_array, happy_array):
    """
    Create a side-by-side comparison of original and happy face.
    """
    # Ensure same size
    h, w = original_array.shape[:2]
    
    # Create canvas for side-by-side comparison
    comparison = np.zeros((h, w * 2 + 20, 3), dtype=np.uint8)
    comparison.fill(255)  # White background
    
    # Place original on left
    comparison[:h, :w] = original_array
    
    # Place happy version on right
    comparison[:h, w + 20:] = happy_array
    
    # Add labels
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(comparison, 'Original', (10, 30), font, 1, (0, 0, 255), 2)
    cv2.putText(comparison, 'Happy Version', (w + 30, 30), font, 1, (0, 255, 0), 2)
    
    return comparison


