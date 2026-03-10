from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.routes import mood_routes, auth_routes, parent_management_routes, child_routes, trusted_routes
# from app.database.story.mongo import mongodb
from app.routes.story import story, ai_story
from app.routes.drawing_routes import router as drawing_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
    """
    Run startup tasks:
    - Create database indexes
    - Backfill missing date_key fields in old mood records
    """
    logger.info("Starting up application...")
    
    # Create database indexes
    from app.database.db import create_indexes
    create_indexes()
    
    # Backfill missing date_key for old moods (runs only once, idempotent)
    from app.services.mood_service import backfill_missing_date_keys
    stats = backfill_missing_date_keys()
    
    if stats["total_found"] > 0:
        logger.info(f"✓ Date_key backfill complete: {stats['updated']} updated, {stats['failed']} failed")
    else:
        logger.info("✓ No moods need backfilling")
    
    logger.info("Application startup complete")

app.include_router(mood_routes.router)
app.include_router(auth_routes.router)
app.include_router(parent_management_routes.router)
app.include_router(child_routes.router)
app.include_router(trusted_routes.router)


app.include_router(story.router)
app.include_router(ai_story.router)

# @app.on_event("startup")
# async def startup():
#     await mongodb.connect()

# @app.on_event("shutdown")
# async def shutdown():
#     await mongodb.close()

# @app.get("/")
# async def root():
#     return {"message": "Welcome to the Story Generation Research Project API"}
app.include_router(drawing_router)

@app.get("/health")
def health():
    return {"ok": True}
