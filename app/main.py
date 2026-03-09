from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.story.mongo import mongodb
from app.routes.story import story, ai_story

app = FastAPI(title="Story Generation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(story.router)
app.include_router(ai_story.router)

@app.on_event("startup")
async def startup():
    await mongodb.connect()

@app.on_event("shutdown")
async def shutdown():
    await mongodb.close()

@app.get("/")
async def root():
    return {"message": "Welcome to the Story Generation Research Project API"}