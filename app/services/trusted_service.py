"""
Trusted Contact Service
Business logic for trusted contact invitations
"""
from datetime import datetime
from typing import Optional, List
import secrets
from bson import ObjectId
from app.database.db import trusted_contacts_col, children_col, parents_col

def generate_invite_token() -> str:
    """Generate a secure random token for invitation"""
    return secrets.token_urlsafe(32)

def create_trusted_contact_invitation(parent_id: str, child_id: str, email: str, relationship: str) -> dict:
    """
    Create a trusted contact invitation
    
    Args:
        parent_id: Parent's ObjectId as string
        child_id: Child's ObjectId as string
        email: Trusted contact email
        relationship: Relationship type (Teacher, Relative, Family Friend, Other)
        
    Returns:
        Created invitation document
    """
    invite_token = generate_invite_token()
    
    invitation_doc = {
        "parent_id": ObjectId(parent_id),
        "child_id": ObjectId(child_id),
        "email": email,
        "relationship": relationship,
        "status": "pending",
        "invite_token": invite_token,
        "invited_at": datetime.utcnow(),
        "accepted_at": None
    }
    
    result = trusted_contacts_col.insert_one(invitation_doc)
    invitation_doc["_id"] = result.inserted_id
    
    return invitation_doc

def get_invitations_for_child(child_id: str, include_removed: bool = False) -> List[dict]:
    """
    Get all trusted contact invitations for a child
    
    Args:
        child_id: Child's ObjectId as string
        include_removed: If True, include removed contacts. Default False.
        
    Returns:
        List of invitation documents
    """
    if not ObjectId.is_valid(child_id):
        return []
    
    query = {"child_id": ObjectId(child_id)}
    
    # Exclude removed contacts by default
    if not include_removed:
        query["status"] = {"$ne": "removed"}
    
    invitations = trusted_contacts_col.find(query)
    return list(invitations)

def get_invitation_by_token(token: str) -> Optional[dict]:
    """
    Get invitation by token
    
    Args:
        token: Invitation token
        
    Returns:
        Invitation document or None
    """
    return trusted_contacts_col.find_one({"invite_token": token})

def accept_invitation(token: str) -> bool:
    """
    Accept a trusted contact invitation
    
    Args:
        token: Invitation token
        
    Returns:
        True if accepted successfully, False otherwise
    """
    result = trusted_contacts_col.update_one(
        {"invite_token": token, "status": "pending"},
        {
            "$set": {
                "status": "accepted",
                "accepted_at": datetime.utcnow()
            }
        }
    )
    
    return result.modified_count > 0

def get_accepted_contacts_for_child(child_id: str) -> List[str]:
    """
    Get all accepted trusted contact emails for a child
    
    Args:
        child_id: Child's ObjectId as string
        
    Returns:
        List of email addresses
    """
    if not ObjectId.is_valid(child_id):
        return []
    
    contacts = trusted_contacts_col.find({
        "child_id": ObjectId(child_id),
        "status": "accepted"
    })
    
    return [contact["email"] for contact in contacts]

def get_parent_and_trusted_emails(child_id: str) -> List[str]:
    """
    Get parent email and all accepted trusted contact emails for a child
    
    Args:
        child_id: Child's ObjectId as string
        
    Returns:
        List of email addresses (parent + trusted contacts)
    """
    if not ObjectId.is_valid(child_id):
        return []
    
    emails = []
    
    # Get child's parent email
    child = children_col.find_one({"_id": ObjectId(child_id)})
    if child:
        parent = parents_col.find_one({"_id": child["parent_id"]})
        if parent:
            emails.append(parent["email"])
    
    # Get all accepted trusted contact emails
    trusted_emails = get_accepted_contacts_for_child(child_id)
    emails.extend(trusted_emails)
    
    return emails

def remove_trusted_contact(parent_id: str, child_id: str, trusted_id: str, reason: str) -> dict:
    """
    Remove a trusted contact (soft delete)
    
    Args:
        parent_id: Parent's ObjectId as string
        child_id: Child's ObjectId as string
        trusted_id: Trusted contact's ObjectId as string
        reason: Reason for removal
        
    Returns:
        Updated trusted contact document
        
    Raises:
        ValueError: If trusted contact not found or doesn't belong to parent/child
    """
    if not ObjectId.is_valid(trusted_id):
        raise ValueError("Invalid trusted contact ID")
    
    # Find the trusted contact
    trusted_contact = trusted_contacts_col.find_one({"_id": ObjectId(trusted_id)})
    
    if not trusted_contact:
        raise ValueError("Trusted contact not found")
    
    # Verify it belongs to the correct parent and child
    if str(trusted_contact["parent_id"]) != parent_id or str(trusted_contact["child_id"]) != child_id:
        raise ValueError("Trusted contact does not belong to this parent/child")
    
    # Check if already removed
    if trusted_contact.get("status") == "removed":
        raise ValueError("Trusted contact already removed")
    
    # Update status to removed
    result = trusted_contacts_col.update_one(
        {"_id": ObjectId(trusted_id)},
        {
            "$set": {
                "status": "removed",
                "removed_reason": reason,
                "removed_at": datetime.utcnow(),
                "removed_by_parent_id": ObjectId(parent_id)
            }
        }
    )
    
    if result.modified_count == 0:
        raise ValueError("Failed to remove trusted contact")
    
    # Return updated document
    updated_contact = trusted_contacts_col.find_one({"_id": ObjectId(trusted_id)})
    return updated_contact
