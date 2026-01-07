from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
import logging
from app.services.ai_service import story_generator
import time

router = APIRouter(prefix="/ai", tags=["ai-story-generation"])
logger = logging.getLogger(__name__)

class StoryRequest(BaseModel):
    """Request model for AI story generation"""
    mood: str = Field(..., description="Emotional state (sad, anxious, empty, calm, happy, angry, confused, hopeful)")
    weather: str = Field(..., description="Weather metaphor (sunny, rainy, stormy, foggy)")
    character: str = Field(..., description="Folk tale character (hare, lion, elephant)")
    starter_sentence: Optional[str] = Field(None, description="Optional starting sentence in Sinhala")
    max_length: Optional[int] = Field(300, ge=50, le=1000, description="Maximum story length")
    temperature: Optional[float] = Field(0.7, ge=0.1, le=1.0, description="Creativity control")
    
    class Config:
        json_schema_extra = {
            "example": {
                "mood": "happy",
                "weather": "sunny", 
                "character": "hare",
                "starter_sentence": "අද දවස මට ගොඩක් සතුටක්",
                "max_length": 300,
                "temperature": 0.7
            }
        }

class StoryResponse(BaseModel):
    """Response model for generated story"""
    success: bool
    story: str
    metadata: dict

@router.post("/generate-story", response_model=StoryResponse)
async def generate_story(request: StoryRequest):
    """
    Generate a story using the AI GRU model.
    """
    try:
        # Validate inputs
        valid_moods = ['sad', 'anxious', 'empty', 'calm', 'happy', 'angry', 'confused', 'hopeful']
        valid_weather = ['sunny', 'rainy', 'stormy', 'foggy']
        valid_characters = ['hare', 'lion', 'elephant']
        
        if request.mood.lower() not in valid_moods:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid mood '{request.mood}'. Must be one of: {valid_moods}"
            )
        
        if request.weather.lower() not in valid_weather:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid weather '{request.weather}'. Must be one of: {valid_weather}"
            )
        
        if request.character.lower() not in valid_characters:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid character '{request.character}'. Must be one of: {valid_characters}"
            )
        
        logger.info(f"Generating story: mood={request.mood}, weather={request.weather}, character={request.character}")
        
        # Generate story using GRU model
        result = story_generator.generate_story(
            mood=request.mood.lower(),
            weather=request.weather.lower(),
            character=request.character.lower(),
            starter_sentence=request.starter_sentence,
            max_length=min(request.max_length, 500),  # Cap at 500 for safety
            temperature=max(0.1, min(request.temperature, 1.0))  # Ensure valid range
        )
        
        return StoryResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Story generation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate story: {str(e)}"
        )

@router.post("/generate-and-save")
async def generate_and_save_story(
    request: StoryRequest,
    background_tasks: BackgroundTasks,
    user_id: Optional[str] = None,
    title: Optional[str] = None
):
    """
    Generate a story and save it to database in background.
    """
    from app.services.story_service import story_service
    
    # Generate story
    result = story_generator.generate_story(
        mood=request.mood,
        weather=request.weather,
        character=request.character,
        starter_sentence=request.starter_sentence,
        max_length=request.max_length
    )
    
    if not result['success']:
        raise HTTPException(status_code=500, detail="Story generation failed")
    
    # Prepare story data for saving
    story_data = {
        "user_id": user_id or "anonymous",
        "title": title or f"{request.character.capitalize()}'s {request.mood.capitalize()} Journey",
        "content": result['story'],
        "mood_profile": {
            "mood": request.mood,
            "weather": request.weather,
            "character": request.character,
            "starter_sentence": request.starter_sentence
        },
        "tags": ["ai-generated", request.mood, request.character],
        "is_public": True,
        "metadata": result['metadata']
    }
    
    # Save in background
    background_tasks.add_task(
        story_service.create_story_from_dict,
        story_data
    )
    
    return {
        "message": "Story generated and queued for saving",
        "story": result['story'],
        "save_status": "queued"
    }

@router.get("/model-info")
async def get_model_info():
    """Get information about the loaded AI model"""
    try:
        info = story_generator.get_model_info()
        return info
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get model info: {str(e)}"
        )

@router.get("/health")
async def ai_health_check():
    """Check if AI service is healthy"""
    try:
        info = story_generator.get_model_info()
        
        if info["status"] == "Loaded":
            return {
                "status": "healthy",
                "model": info["model_type"],
                "timestamp": time.time()
            }
        else:
            return {
                "status": "unhealthy",
                "reason": "Model not loaded",
                "timestamp": time.time()
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "reason": str(e),
            "timestamp": time.time()
        }