"""
Parent Management Routes
Handles parent operations: creating children, managing trusted contacts
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.schemas.auth_schema import TokenData
from app.schemas.parent_child_schema import (
    ChildCreateRequest,
    ChildResponse,
    ChildListResponse,
    TrustedContactInviteRequest,
    TrustedContactResponse,
    TrustedContactRemoveRequest
)
from app.services.auth_service import get_current_parent
from app.services.child_service import create_child, verify_child_belongs_to_parent
from app.services.parent_service import get_parent_children
from app.services.trusted_service import (
    create_trusted_contact_invitation,
    get_invitations_for_child,
    remove_trusted_contact
)
from app.services.email_service import send_trusted_contact_invitation, send_trusted_contact_removed_email
from bson import ObjectId

router = APIRouter(prefix="/parent", tags=["Parent Management"])

@router.post("/children", response_model=ChildResponse)
def create_child_account(
    request: ChildCreateRequest,
    current_parent: TokenData = Depends(get_current_parent)
):
    """
    Create a new child account under the parent
    
    Example request:
    ```json
    {
      "username": "child_user",
      "password": "childpass123",
      "name": "John Doe",
      "age": 10
    }
    ```
    """
    try:
        child = create_child(
            parent_id=current_parent.id,
            username=request.username,
            password=request.password,
            name=request.name,
            age=request.age
        )
        
        return ChildResponse(
            id=str(child["_id"]),
            username=child["username"],
            name=child["name"],
            age=child["age"],
            alerts_consent=child["alerts_consent"],
            parent_id=str(child["parent_id"]),
            created_at=child["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create child: {str(e)}"
        )

@router.get("/children", response_model=List[ChildListResponse])
def list_children(current_parent: TokenData = Depends(get_current_parent)):
    """
    Get list of all children for the current parent
    """
    try:
        children = get_parent_children(current_parent.id)
        
        return [
            ChildListResponse(
                id=str(child["_id"]),
                username=child["username"],
                name=child["name"],
                age=child["age"],
                alerts_consent=child["alerts_consent"]
            )
            for child in children
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch children: {str(e)}"
        )

@router.post("/children/{child_id}/trusted", response_model=TrustedContactResponse)
def invite_trusted_contact(
    child_id: str,
    request: TrustedContactInviteRequest,
    current_parent: TokenData = Depends(get_current_parent)
):
    """
    Invite a trusted contact for a specific child
    
    Example request:
    ```json
    {
      "email": "trusted@example.com",
      "relationship": "Teacher"
    }
    ```
    """
    try:
        # Verify child belongs to parent
        if not verify_child_belongs_to_parent(child_id, current_parent.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Child does not belong to this parent"
            )
        
        # Create invitation
        invitation = create_trusted_contact_invitation(
            parent_id=current_parent.id,
            child_id=child_id,
            email=request.email,
            relationship=request.relationship
        )
        
        # Get child name for email
        from app.services.child_service import get_child_by_id
        child = get_child_by_id(child_id)
        child_name = child["name"] if child else "the child"
        
        # Send invitation email
        send_trusted_contact_invitation(
            to_email=request.email,
            child_name=child_name,
            token=invitation["invite_token"]
        )
        
        return TrustedContactResponse(
            id=str(invitation["_id"]),
            email=invitation["email"],
            relationship=invitation["relationship"],
            status=invitation["status"],
            invited_at=invitation["invited_at"],
            accepted_at=invitation["accepted_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invite trusted contact: {str(e)}"
        )

@router.get("/children/{child_id}/trusted", response_model=List[TrustedContactResponse])
def list_trusted_contacts(
    child_id: str,
    current_parent: TokenData = Depends(get_current_parent)
):
    """
    Get list of all trusted contact invitations for a specific child
    (excludes removed contacts by default)
    """
    try:
        # Verify child belongs to parent
        if not verify_child_belongs_to_parent(child_id, current_parent.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Child does not belong to this parent"
            )
        
        invitations = get_invitations_for_child(child_id, include_removed=False)
        
        return [
            TrustedContactResponse(
                id=str(inv["_id"]),
                email=inv["email"],
                relationship=inv.get("relationship", "Other"),  # Default for old records
                status=inv["status"],
                invited_at=inv["invited_at"],
                accepted_at=inv["accepted_at"]
            )
            for inv in invitations
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trusted contacts: {str(e)}"
        )

@router.post("/children/{child_id}/trusted/{trusted_id}/remove")
def remove_trusted_contact_endpoint(
    child_id: str,
    trusted_id: str,
    request: TrustedContactRemoveRequest,
    current_parent: TokenData = Depends(get_current_parent)
):
    """
    Remove a trusted contact (soft delete with reason)
    
    Works for both pending and accepted contacts.
    Sends notification email to the removed contact.
    
    Example request:
    ```json
    {
      "reason": "No longer needed as the child has graduated"
    }
    ```
    """
    try:
        # Verify child belongs to parent
        if not verify_child_belongs_to_parent(child_id, current_parent.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Child does not belong to this parent"
            )
        
        # Validate reason
        if len(request.reason.strip()) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reason must be at least 3 characters long"
            )
        
        # Remove the trusted contact
        try:
            updated_contact = remove_trusted_contact(
                parent_id=current_parent.id,
                child_id=child_id,
                trusted_id=trusted_id,
                reason=request.reason
            )
        except ValueError as e:
            error_message = str(e)
            if "not found" in error_message or "does not belong" in error_message:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_message
                )
            elif "already removed" in error_message:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_message
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot remove trusted contact: {error_message}"
                )
        
        # Get child name for email
        from app.services.child_service import get_child_by_id
        child = get_child_by_id(child_id)
        child_name = child["name"] if child else "the child"
        
        # Send removal notification email
        send_trusted_contact_removed_email(
            to_email=updated_contact["email"],
            child_name=child_name,
            reason=request.reason
        )
        
        return {
            "status": "success",
            "message": "Trusted contact removed successfully",
            "data": {
                "id": str(updated_contact["_id"]),
                "email": updated_contact["email"],
                "status": updated_contact["status"],
                "removed_at": updated_contact.get("removed_at")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove trusted contact: {str(e)}"
        )
