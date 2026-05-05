from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.routes import (
    mood_routes,
    auth_routes,
    parent_management_routes,
    child_routes,
    trusted_routes,
    music_routes,
    leaderboard_routes,
    emotion_routes,
)

from app.routes.story import story, ai_story
from app.routes.drawing_routes import router as drawing_router
from app.routes.theraphy_routes import router as therapy_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Children Mental Health API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up application...")

    from app.database.db import create_indexes
    create_indexes()

    from app.services.mood_service import backfill_missing_date_keys
    stats = backfill_missing_date_keys()

    if stats["total_found"] > 0:
        logger.info(
            f"✓ Date_key backfill complete: "
            f"{stats['updated']} updated, {stats['failed']} failed"
        )
    else:
        logger.info("✓ No moods need backfilling")

    logger.info("Application startup complete")


app.include_router(mood_routes.router)
app.include_router(auth_routes.router)
app.include_router(parent_management_routes.router)
app.include_router(child_routes.router)
app.include_router(trusted_routes.router)
app.include_router(music_routes.router)
app.include_router(leaderboard_routes.router)
app.include_router(emotion_routes.router)

app.include_router(story.router)
app.include_router(ai_story.router)

app.include_router(drawing_router)

# ✅ THIS WAS MISSING
app.include_router(therapy_router)


@app.get("/health")
def health():
    return {"ok": True}