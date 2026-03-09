from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Literal
import logging
from app.services.story.ai_service import story_generator
import time

router = APIRouter(prefix="/ai", tags=["ai-story-generation"])
logger = logging.getLogger(__name__)

class StoryRequest(BaseModel):
    """Request model for AI story generation"""
    mood: str = Field(..., description="Emotional state (sad, anxious, empty, calm, happy, angry, confused, hopeful)")
    weather: str = Field(..., description="Weather metaphor (sunny, rainy, stormy, foggy)")
    character: str = Field(..., description="Folk tale character (hare, lion, elephant)")
    starter_sentence: Optional[str] = Field(None, description="Optional starting sentence in Sinhala")
    story_length: Literal['short', 'medium', 'long'] = Field('medium', description="Story length: short, medium, or long")
    temperature: Optional[float] = Field(0.7, ge=0.1, le=1.0, description="Creativity control")
    
    class Config:
        json_schema_extra = {
            "example": {
                "mood": "happy",
                "weather": "sunny", 
                "character": "hare",
                "starter_sentence": "අද දවස මට ගොඩක් සතුටක්",
                "story_length": "medium",
                "temperature": 0.7
            }
        }

class EnhancedStoryResponse(BaseModel):
    """Enhanced response model for generated story with moral lesson"""
    success: bool
    title: str
    story: str
    moral_lesson: dict
    story_type: str
    metadata: dict

@router.post("/generate-story", response_model=EnhancedStoryResponse)
async def generate_story(request: StoryRequest):
    """
    Generate a meaningful Sinhala folk tale using the enhanced AI model.
    """
    try:
        # Validate inputs
        valid_moods = ['sad', 'anxious', 'empty', 'calm', 'happy', 'angry', 'confused', 'hopeful']
        valid_weather = ['sunny', 'rainy', 'stormy', 'foggy']
        valid_characters = ['hare', 'lion', 'elephant']
        valid_story_lengths = ['short', 'medium', 'long']
        
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
        
        if request.story_length.lower() not in valid_story_lengths:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid story length '{request.story_length}'. Must be one of: {valid_story_lengths}"
            )
        
        logger.info(f"Generating enhanced story: mood={request.mood}, weather={request.weather}, character={request.character}, length={request.story_length}")
        
        # Generate story using enhanced model
        result = story_generator.generate_story(
            mood=request.mood.lower(),
            weather=request.weather.lower(),
            character=request.character.lower(),
            starter_sentence=request.starter_sentence,
            story_length=request.story_length.lower(),
            temperature=max(0.1, min(request.temperature, 1.0))  # Ensure valid range
        )
        
        if not result.get('success', False):
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Failed to generate story')
            )
        
        return EnhancedStoryResponse(**result)
        
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
        story_length=request.story_length
    )
    
    if not result['success']:
        raise HTTPException(status_code=500, detail="Story generation failed")
    
    # Prepare story data for saving
    story_data = {
        "user_id": user_id or "anonymous",
        "title": title or result.get('title', f"{request.character.capitalize()}'s {request.mood.capitalize()} Journey"),
        "content": result['story'],
        "mood_profile": {
            "mood": request.mood,
            "weather": request.weather,
            "character": request.character,
            "starter_sentence": request.starter_sentence,
            "story_length": request.story_length
        },
        "tags": [
            "ai-generated", 
            "folk-tale",
            request.mood, 
            request.character,
            f"length-{request.story_length}"
        ],
        "moral_lesson": result.get('moral_lesson', {}),
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
        "title": result.get('title', ''),
        "story_preview": result['story'][:100] + "..." if len(result['story']) > 100 else result['story'],
        "moral_lesson": result.get('moral_lesson', {}).get('teaching', ''),
        "save_status": "queued"
    }

@router.get("/story-templates")
async def get_story_templates():
    """Get available story templates for folk tales"""
    try:
        templates = story_generator.folk_tale_templates
        return {
            "success": True,
            "templates": {
                "available_templates": list(templates.keys()),
                "template_details": templates
            }
        }
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get story templates: {str(e)}"
        )

@router.get("/moral-lessons")
async def get_moral_lessons(moods: Optional[str] = None):
    """Get moral lessons for specific moods"""
    try:
        if hasattr(story_generator, 'moral_lessons'):
            all_lessons = story_generator.moral_lessons
            
            if moods:
                requested_moods = [m.strip() for m in moods.split(',') if m.strip()]
                filtered_lessons = {
                    mood: all_lessons.get(mood)
                    for mood in requested_moods
                    if mood in all_lessons
                }
                return {
                    "success": True,
                    "lessons": filtered_lessons,
                    "total_moods": len(filtered_lessons)
                }
            else:
                return {
                    "success": True,
                    "lessons": all_lessons,
                    "available_moods": list(all_lessons.keys()),
                    "total_moods": len(all_lessons)
                }
        else:
            raise HTTPException(
                status_code=404,
                detail="Moral lessons not available in current model"
            )
            
    except Exception as e:
        logger.error(f"Error getting moral lessons: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get moral lessons: {str(e)}"
        )

@router.get("/model-info")
async def get_model_info():
    """Get information about the loaded AI model"""
    try:
        info = story_generator.get_model_info()
        return {
            "success": True,
            "info": info,
            "timestamp": time.time()
        }
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
        
        status_key = "status" if "status" in info else "model_status"
        
        if info.get(status_key, "").lower() in ["active", "loaded", "ready"]:
            return {
                "status": "healthy",
                "model": info.get("model_type", "Unknown"),
                "story_types": list(story_generator.folk_tale_templates.keys()) if hasattr(story_generator, 'folk_tale_templates') else [],
                "supports_long_stories": info.get("supports_long_stories", False),
                "timestamp": time.time()
            }
        else:
            return {
                "status": "unhealthy",
                "reason": "Model not loaded properly",
                "timestamp": time.time()
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "reason": str(e),
            "timestamp": time.time()
        }

# Optional: For backward compatibility with old frontend
class LegacyStoryRequest(BaseModel):
    """Legacy request model for backward compatibility"""
    mood: str
    weather: str
    character: str
    starter_sentence: Optional[str] = None
    max_length: Optional[int] = 300

@router.post("/generate-story-legacy")
async def generate_story_legacy(request: LegacyStoryRequest):
    """
    Legacy endpoint for backward compatibility with max_length parameter.
    Converts max_length to story_length automatically.
    """
    try:
        # Convert max_length to story_length
        if request.max_length <= 150:
            story_length = 'short'
        elif request.max_length <= 300:
            story_length = 'medium'
        else:
            story_length = 'long'
        
        # Generate story using story_length
        result = story_generator.generate_story(
            mood=request.mood.lower(),
            weather=request.weather.lower(),
            character=request.character.lower(),
            starter_sentence=request.starter_sentence,
            story_length=story_length,
            max_length=request.max_length  # Pass for backward compatibility
        )
        
        if not result.get('success', False):
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Failed to generate story')
            )
        
        return EnhancedStoryResponse(**result)
        
    except Exception as e:
        logger.error(f"Legacy story generation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate story: {str(e)}"
        )