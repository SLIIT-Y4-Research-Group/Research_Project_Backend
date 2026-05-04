# Project Full Documentation

## 1. Overview
This project is a FastAPI backend for a children mental health research system. It supports:
- Parent/child authentication and account management
- Child mood tracking and scoring
- Alert workflow with trusted contacts and email notifications
- Emotion prediction from images and "happy-face" transformation
- Drawing analysis (emotion/color/stroke/spatial/object detection)
- Music track upload and mood tagging
- Story generation and story storage APIs
- Leaderboard APIs for game-like scoring

Runtime stack:
- Python + FastAPI + Uvicorn
- MongoDB (`pymongo`) for primary collections
- Motor (async MongoDB) for story module
- ML/AI libs: Torch, TensorFlow, Transformers, Ultralytics YOLO, Gemini API integration

## 2. Repository Structure
- `app/main.py`: API entrypoint and router registration
- `app/core/`: config and security helpers
- `app/database/db.py`: synchronous MongoDB client + collections + indexes
- `app/database/story/mongo.py`: async MongoDB client for story module
- `app/routes/`: all REST endpoints
- `app/services/`: business logic and ML pipelines
- `app/schemas/`: Pydantic models
- `app/models/`: model artifacts (`.pt`)
- `models/story/`: tokenizer/model files for story generation
- `requirements.txt`: dependencies
- `API_EXAMPLES.md`: curl examples

## 3. Application Startup Flow
From `app/main.py`:
1. Loads `.env` using `python-dotenv`
2. Builds FastAPI app (`Children Mental Health API`, version `1.0.0`)
3. Enables permissive CORS:
   - `allow_origins=["*"]`
   - `allow_methods=["*"]`
   - `allow_headers=["*"]`
4. On startup:
   - Calls `create_indexes()` from `app.database.db`
   - Calls `backfill_missing_date_keys()` from `app.services.mood_service`
5. Includes all routers
6. Exposes `GET /health` returning `{ "ok": true }`

## 4. Environment Variables
Configured in `app/core/config.py`:
- `MONGO_URI`
- `MONGO_DB_NAME`
- `EMOTION_MODEL_PATH`
- `YOLO_MODEL_PATH`
- `ENABLE_OBJECT_DETECTION`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `JWT_EXPIRE_MINUTES`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASS`
- `FROM_EMAIL`
- `FRONTEND_BASE_URL`
- `BACKEND_BASE_URL`
- `BAD_MOOD_THRESHOLD`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`
- `GEMINI_API_KEY`

Recommended `.env` template:
```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=research_project
JWT_SECRET=change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
FROM_EMAIL=
FRONTEND_BASE_URL=http://localhost:3000
BACKEND_BASE_URL=http://localhost:8000
BAD_MOOD_THRESHOLD=5
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
GEMINI_API_KEY=
```

## 5. Database Model and Collections
Primary DB collections from `app/database/db.py`:
- `parents`
- `children`
- `trusted_contacts`
- `moods`
- `tracks`
- `leaderboard`
- `drawing_analyses`

Story module collection (async):
- `stories` (via `app/services/story/story_service.py`)

Indexes created:
- `parents.email` unique
- `children.username` unique
- `children.parent_id`
- `trusted_contacts.invite_token` unique sparse
- `trusted_contacts.child_id`
- `trusted_contacts.email`
- `moods.child_id + datetime`
- `moods.child_id + date_key` unique partial (one mood per day)
- `tracks.created_at`
- `leaderboard.score` desc, `created_at`, `player_name`

## 6. Authentication and Authorization
JWT-based auth (`app/services/auth_service.py`):
- Password hashing with `passlib` bcrypt
- Bearer token decoding via `python-jose`
- Role claims (`parent` or `child`)

Dependencies:
- `get_current_user`
- `get_current_parent`
- `get_current_child`

Token payload fields used:
- `id`
- `role`
- optional `email` / `username`

## 7. API Catalog
Base URL (local): `http://localhost:8000`

### 7.1 Auth (`/auth`)
- `POST /auth/parent/register`
- `POST /auth/parent/login`
- `POST /auth/child/login`

### 7.2 Parent Management (`/parent`)
- `POST /parent/children`
- `GET /parent/children`
- `POST /parent/children/{child_id}/trusted`
- `GET /parent/children/{child_id}/trusted`
- `POST /parent/children/{child_id}/trusted/{trusted_id}/remove`
- `GET /parent/drawings`

### 7.3 Child (`/child`)
- `GET /child/me`
- `PATCH /child/me/consent`
- `GET /child/me/today-mood-status`
- `GET /child/me/weekly-moods`

### 7.4 Mood (`/mood`)
- `POST /mood/checkin`
- `POST /mood/store`
- `POST /mood/predict`
- `POST /mood/predict_question`
- `POST /mood/validate_answer`
- `POST /mood/predict_overall`
- `POST /mood/respond_alert_permission`

Important behavior in `/mood/store`:
- Enforces one mood per child per day (`date_key` unique)
- Returns `already_exists` if mood already submitted today
- Triggers pending alert flow when bad mood threshold is reached

### 7.5 Trusted Contact (`/trusted`)
- `GET /trusted/accept?token=...`
- Returns HTML pages for success/error/already accepted

### 7.6 Emotion (`/emotion`)
- `POST /emotion/predict` (preprocessed array)
- `POST /emotion/predict-image` (base64 image)
- `POST /emotion/upload` (multipart image)
- `POST /emotion/predict-with-happy-face`
- `POST /emotion/upload-with-happy-face`

### 7.7 Drawing Analysis (`/drawing`)
- `POST /drawing/analyze` (multipart: `child_id`, optional `note`, `image`)
- Runs preprocess + feature extraction + emotion + optional object detection
- Saves result to `drawing_analyses`

### 7.8 Music (`/music`)
- `POST /music/tracks`
- Multipart upload for audio + cover image
- Upload target: Cloudinary

### 7.9 Leaderboard (`/leaderboard`)
- `POST /leaderboard`
- `GET /leaderboard/top`
- `GET /leaderboard`
- `GET /leaderboard/player/{player_name}`
- `GET /leaderboard/{entry_id}`
- `DELETE /leaderboard/{entry_id}`

### 7.10 Stories (`/stories` and `/ai`)
Story storage:
- `POST /stories/`
- `GET /stories/user/{user_id}`
- `GET /stories/public/`
- `GET /stories/{story_id}`

AI story generation:
- `POST /ai/generate-story`
- `POST /ai/generate-and-save`
- `GET /ai/story-templates`
- `GET /ai/moral-lessons`
- `GET /ai/model-info`
- `POST /ai/generate-story-legacy`

## 8. Core Service Modules
- `parent_service.py`: parent CRUD/auth
- `child_service.py`: child CRUD/auth/consent/pending-alert state
- `trusted_service.py`: token invitation lifecycle and contact linking
- `email_service.py`: SMTP email sending + invitation/alert templates
- `mood_service.py`: daily mood creation/query/backfill logic
- `emotion_model_service.py`: emotion prediction provider abstraction
- `face_generation_service.py`: happy-face generation pipeline
- `drawing_service.py`: parent drawing retrieval
- `analysis_service.py`: drawing color/stroke/spatial features
- `preprocess.py`: scan/canvas preprocessing
- `object_detection.py`: YOLO-based object detection
- `music_service.py`: Cloudinary upload + track persistence
- `story/ai_service.py`: Gemini-backed Sinhala story generation
- `story/story_service.py`: async story persistence/query

## 9. ML/AI Assets and Dependencies
Model files:
- `app/models/best_newart_4class_b2.pt` (emotion)
- `app/models/best.pt` (YOLO object detection)
- `models/story/*.pickle` tokenizers

Notable dependencies:
- `torch`, `torchvision`, `tensorflow`, `transformers`, `ultralytics`
- `google-generativeai`

## 10. Running the Project
1. Create and activate virtualenv
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Add `.env` values
4. Start API:
   - `uvicorn app.main:app --reload`
5. Open docs:
   - `http://localhost:8000/docs`
   - `http://localhost:8000/redoc`

## 11. Testing and Validation
Artifacts present:
- `API_EXAMPLES.md`: endpoint testing examples
- `test_validator.py`: validator-related checks
- `test_request.json`: request sample payload

Recommended test checklist:
- Parent register/login
- Child create/login
- Mood daily duplicate protection
- Alert threshold + permission response flow
- Trusted invitation accept link
- Emotion image upload paths
- Drawing analysis insert pipeline
- Story generation + persistence
- Music upload (requires Cloudinary config)

## 12. Current Technical Risks / Notes
- `.env` currently contains real credentials in repository workspace; rotate and replace with secrets manager values.
- CORS is fully open (`*`) which is not production-safe.
- `app/services/auth_service.py` prints bcrypt module debug info at import time.
- `app/database/db.py` calls `create_indexes()` on import and also startup; function is mostly idempotent but runs more than once.
- Story module connection startup hooks are commented out in `app/main.py`; story APIs depend on async `mongodb.connect()` initialization path.
- There are two emotion route files (`emotion.py` and `emotion_routes.py`), but only `emotion_routes.py` is registered.

## 13. Recommended Production Hardening
1. Move all credentials to secret manager and rotate compromised values.
2. Restrict CORS to trusted frontend origins.
3. Enforce stronger password policy and rate limiting on auth endpoints.
4. Add request logging with PII redaction.
5. Add automated tests for all critical flows and CI validation.
6. Add health checks for DB and model availability.
7. Standardize sync/async DB usage and ensure story DB startup connection is active.

## 14. Useful Files Quick Reference
- `app/main.py`
- `app/core/config.py`
- `app/database/db.py`
- `app/routes/*.py`
- `app/routes/story/*.py`
- `app/services/*.py`
- `app/services/story/*.py`
- `API_EXAMPLES.md`
- `requirements.txt`

---
Generated from current codebase state on 2026-04-30.
