"""
Authentication Routes
Handles parent and child registration/login
"""
from fastapi import APIRouter, HTTPException, status
from app.schemas.auth_schema import (
    ParentRegisterRequest,
    ParentLoginRequest,
    ChildLoginRequest,
    TokenResponse
)
from app.services.parent_service import create_parent, authenticate_parent
from app.services.child_service import authenticate_child
from app.services.auth_service import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/parent/register", response_model=TokenResponse)
def register_parent(request: ParentRegisterRequest):
    """
    Register a new parent account
    
    Example request:
    ```json
    {
      "email": "parent@example.com",
      "password": "securepass123"
    }
    ```
    """
    try:
        # Explicitly extract password as string
        password_str = str(request.password)
        email_str = str(request.email)
        
        parent = create_parent(email_str, password_str)
        
        # Create JWT token
        token_data = {
            "id": str(parent["_id"]),
            "role": "parent",
            "email": parent["email"]
        }
        access_token = create_access_token(token_data)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            parent={
                "id": str(parent["_id"]),
                "email": parent["email"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/parent/login", response_model=TokenResponse)
def login_parent(request: ParentLoginRequest):
    """
    Parent login
    
    Example request:
    ```json
    {
      "email": "parent@example.com",
      "password": "securepass123"
    }
    ```
    """
    parent = authenticate_parent(request.email, request.password)
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create JWT token
    token_data = {
        "id": str(parent["_id"]),
        "role": "parent",
        "email": parent["email"]
    }
    access_token = create_access_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        parent={
            "id": str(parent["_id"]),
            "email": parent["email"]
        }
    )

@router.post("/child/login", response_model=TokenResponse)
def login_child(request: ChildLoginRequest):
    """
    Child login
    
    Example request:
    ```json
    {
      "username": "child_user",
      "password": "childpass123"
    }
    ```
    """
    child = authenticate_child(request.username, request.password)
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Create JWT token
    token_data = {
        "id": str(child["_id"]),
        "role": "child",
        "username": child["username"]
    }
    access_token = create_access_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        child={
            "id": str(child["_id"]),
            "username": child["username"],
            "name": child["name"]
        }
    )
