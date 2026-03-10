"""
Child Routes
Handles child-specific operations: profile, consent management
"""
from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.auth_schema import TokenData
from app.schemas.parent_child_schema import (
    ChildProfileResponse,
    ChildConsentUpdate
)
from app.schemas.mood_schema import TodayMoodStatusResponse, WeeklyMoodsResponse, WeeklyMoodDay, WeeklyMoodSummary
from app.services.auth_service import get_current_child
from app.services.child_service import get_child_by_id, update_child_consent
from app.services.mood_service import get_today_mood_for_child, get_weekly_moods_for_child, get_today_date_key
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/child", tags=["Child Management"])

@router.get("/me", response_model=ChildProfileResponse)
def get_child_profile(current_child: TokenData = Depends(get_current_child)):
    """
    Get current child's profile
    """
    try:
        child = get_child_by_id(current_child.id)
        
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found"
            )
        
        return ChildProfileResponse(
            id=str(child["_id"]),
            username=child["username"],
            name=child["name"],
            age=child["age"],
            alerts_consent=child["alerts_consent"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch profile: {str(e)}"
        )

@router.patch("/me/consent")
def update_consent(
    request: ChildConsentUpdate,
    current_child: TokenData = Depends(get_current_child)
):
    """
    Update child's alert consent setting
    
    Example request:
    ```json
    {
      "alerts_consent": true
    }
    ```
    """
    try:
        success = update_child_consent(current_child.id, request.alerts_consent)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update consent"
            )
        
        status_text = "enabled" if request.alerts_consent else "disabled"
        
        return {
            "status": "success",
            "message": f"Alerts consent {status_text}",
            "alerts_consent": request.alerts_consent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update consent: {str(e)}"
        )


@router.get("/me/today-mood-status", response_model=TodayMoodStatusResponse)
def get_today_mood_status(current_child: TokenData = Depends(get_current_child)):
    """
    Check if child has already completed today's mood check-in
    
    Returns:
    - completed: bool - whether today's mood is recorded
    - date: str - today's date (YYYY-MM-DD)
    - mood: str | null - mood value if completed
    - datetime: datetime | null - timestamp if completed
    
    Example responses:
    ```json
    // Completed
    {
      "completed": true,
      "date": "2026-03-10",
      "mood": "Happy",
      "recorded_at": "2026-03-10T09:30:00"
    }
    
    // Not completed
    {
      "completed": false,
      "date": "2026-03-10",
      "mood": null,
      "recorded_at": null
    }
    ```
    """
    try:
        logger.debug(f"GET /child/me/today-mood-status - child_id: {current_child.id}")
        
        today_date = get_today_date_key()
        mood_record = get_today_mood_for_child(current_child.id)
        
        if mood_record:
            logger.debug(f"Today's mood found for child {current_child.id}: {mood_record.get('mood')}")
            return TodayMoodStatusResponse(
                completed=True,
                date=today_date,
                mood=mood_record["mood"],
                recorded_at=mood_record["datetime"]
            )
        else:
            logger.debug(f"No mood found for child {current_child.id} on {today_date}")
            return TodayMoodStatusResponse(
                completed=False,
                date=today_date,
                mood=None,
                recorded_at=None
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch today's mood status: {str(e)}"
        )


@router.get("/me/weekly-moods", response_model=WeeklyMoodsResponse)
def get_weekly_moods(current_child: TokenData = Depends(get_current_child)):
    """
    Get child's mood history for the last 7 days
    
    Returns complete 7-day history including days with no recorded mood.
    Days are ordered from oldest to newest (7 days ago → today).
    
    Response includes:
    - days: array of 7 days with mood data
    - summary: count of happy, normal, bad, and missed days
    
    Example response:
    ```json
    {
      "days": [
        {"date": "2026-03-04", "mood": "Happy", "completed": true, "recorded_at": "2026-03-04T10:00:00"},
        {"date": "2026-03-05", "mood": "Normal", "completed": true, "recorded_at": "2026-03-05T09:30:00"},
        {"date": "2026-03-06", "mood": "Bad", "completed": true, "recorded_at": "2026-03-06T11:00:00"},
        {"date": "2026-03-07", "mood": null, "completed": false, "recorded_at": null},
        {"date": "2026-03-08", "mood": "Happy", "completed": true, "recorded_at": "2026-03-08T10:15:00"},
        {"date": "2026-03-09", "mood": "Normal", "completed": true, "recorded_at": "2026-03-09T09:45:00"},
        {"date": "2026-03-10", "mood": null, "completed": false, "recorded_at": null}
      ],
      "summary": {
        "happy": 2,
        "normal": 2,
        "bad": 1,
        "missed": 2
      }
    }
    ```
    """
    try:
        logger.debug(f"GET /child/me/weekly-moods - child_id: {current_child.id}")
        
        weekly_data = get_weekly_moods_for_child(current_child.id, days=7)
        
        # Calculate summary statistics
        happy_count = sum(1 for day in weekly_data if day["mood"] and day["mood"].lower() == "happy")
        normal_count = sum(1 for day in weekly_data if day["mood"] and day["mood"].lower() == "normal")
        bad_count = sum(1 for day in weekly_data if day["mood"] and day["mood"].lower() == "bad")
        missed_count = sum(1 for day in weekly_data if not day["completed"])
        
        logger.debug(f"Weekly mood summary for child {current_child.id}: happy={happy_count}, normal={normal_count}, bad={bad_count}, missed={missed_count}")
        
        # Convert to Pydantic models - map 'datetime' to 'recorded_at'
        days = [
            WeeklyMoodDay(
                date=day["date"],
                mood=day["mood"],
                completed=day["completed"],
                recorded_at=day["datetime"]
            ) for day in weekly_data
        ]
        summary = WeeklyMoodSummary(
            happy=happy_count,
            normal=normal_count,
            bad=bad_count,
            missed=missed_count
        )
        
        return WeeklyMoodsResponse(days=days, summary=summary)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch weekly moods: {str(e)}"
        )
