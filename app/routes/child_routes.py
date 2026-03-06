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
from app.services.auth_service import get_current_child
from app.services.child_service import get_child_by_id, update_child_consent

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
