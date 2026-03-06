import os

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "research_project")


EMOTION_MODEL_PATH = os.getenv(
    "EMOTION_MODEL_PATH",
    r"E:\a_4th_yr\Research\a_suwa_manasa\Research_Project_Backend\app\models\best_newart_4class_b2.pt"
)
# Optional: turn object detection on/off (pretrained COCO model)
ENABLE_OBJECT_DETECTION = os.getenv("ENABLE_OBJECT_DETECTION", "true").lower() == "true"

import os
print("CONFIG MONGO_URI =", os.getenv("MONGO_URI"))