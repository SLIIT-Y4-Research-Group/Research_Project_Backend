from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.mongo import mongodb
from app.routes import story, health, ai_story
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    logger.info("Starting Story Generation API...")

    # Connect to MongoDB
    await mongodb.connect()

    # Initialize AI model in a separate thread to avoid blocking
    loop = asyncio.get_running_loop()
    try:
        from app.services.ai_service import story_generator
        model_info = await loop.run_in_executor(None, story_generator.get_model_info)
        logger.info(f"AI Model initialized: {model_info.get('model_type', 'Unknown')}")
    except Exception as e:
        logger.error(f"Failed to initialize AI model: {e}")

    # Yield control to the app
    yield

    # Shutdown
    logger.info("Shutting down...")
    await mongodb.close()

# Create FastAPI app
app = FastAPI(
    title="Story Generation API",
    description="Backend for the StoryGen Research Project with GRU AI Story Generation",
    version="1.0.0",
    lifespan=lifespan
)

origins = [
    "http://localhost:53227",  # Your Flutter web app
    "http://localhost:5173",   # Sometimes Vite/other dev servers
]
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(story.router)
app.include_router(health.router)
app.include_router(ai_story.router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Story Generation Research Project API",
        "version": "1.0.0",
        "ai_capabilities": True,
        "model": "GRU (best_gru_model.h5)",
        "endpoints": {
            "ai_story_generation": "/ai/generate-story",
            "stories": "/stories/",
            "health": "/health",
            "docs": "/docs"
        }
    }
