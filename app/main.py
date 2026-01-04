from fastapi import FastAPI
from app.routes import mood_routes
from app.routes import emotion_routes  # new

app = FastAPI(title="Children Mental Health API", version="1.0.0")

# Include existing mood routes
app.include_router(mood_routes.router)

# Include emotion detection routes
app.include_router(emotion_routes.router, prefix="/emotion", tags=["Emotion"])
