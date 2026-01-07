from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import mood_routes
from app.routes import emotion_routes  # new

app = FastAPI(title="Children Mental Health API", version="1.0.0")

# Configure CORS to allow Flutter app to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include existing mood routes
app.include_router(mood_routes.router)

# Include emotion detection routes
app.include_router(emotion_routes.router, prefix="/emotion", tags=["Emotion"])
