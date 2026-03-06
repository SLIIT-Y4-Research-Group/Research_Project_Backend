from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from app.routes import mood_routes
from app.routes.drawing_routes import router as drawing_router

app = FastAPI(title="Children Mental Health API", version="1.0.0")

app.include_router(mood_routes.router)
app.include_router(drawing_router)

@app.get("/health")
def health():
    return {"ok": True}