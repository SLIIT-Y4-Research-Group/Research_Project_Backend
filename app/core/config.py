import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent   # app/
PROJECT_ROOT = BASE_DIR.parent                      # backend/
MODEL_DIR = BASE_DIR / "models"


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip().lower()
    return value in {"true", "1", "yes", "y"}

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "research_project")

EMOTION_MODEL_PATH = os.getenv(
    "EMOTION_MODEL_PATH",
    str(MODEL_DIR / "best_newart_4class_b2.pt")
)

YOLO_MODEL_PATH = os.getenv(
    "YOLO_MODEL_PATH",
    str(MODEL_DIR / "best.pt")
)

PRODUCTION = _env_flag("PRODUCTION", False)
LOCAL_MODEL_PATH = os.getenv(
    "LOCAL_MODEL_PATH",
    str(BASE_DIR / "ml" / "model" / "final_sinhala_mood_model")
)
AWS_MODEL_PATH = os.getenv("AWS_MODEL_PATH", "")
MOOD_MODEL_PATH = AWS_MODEL_PATH if PRODUCTION else LOCAL_MODEL_PATH

ENABLE_OBJECT_DETECTION = os.getenv(
    "ENABLE_OBJECT_DETECTION",
    "true"
).lower() == "true"

JWT_SECRET = os.getenv("JWT_SECRET", "change-this-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "")

FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")

# Alert Configuration
BAD_MOOD_THRESHOLD = int(os.getenv("BAD_MOOD_THRESHOLD", "3"))  # Alert if >= 3 bad moods in 7 days (lowered from 5)

# Cloudinary
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
