"""
Child Service
Business logic for child operations
"""
from datetime import datetime
from typing import Optional
from bson import ObjectId
from fastapi import HTTPException, status
import logging

from app.database.db import children_col
from app.services.auth_service import hash_password, verify_password

logger = logging.getLogger(__name__)

def create_child(parent_id: str, username: str, password: str, name: str, age: int) -> dict:
    """
    Create a new child account under a parent
    
    Args:
        parent_id: Parent's ObjectId as string
        username: Child username (must be unique)
        password: Plain text password (will be hashed)
        name: Child's name
        age: Child's age
        
    Returns:
        Created child document
        
    Raises:
        HTTPException: If username already exists or parent_id invalid
    """
    # Validate parent_id
    if not ObjectId.is_valid(parent_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid parent ID"
        )
    
    # Check if username already exists
    existing = children_col.find_one({"username": username})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create child document
    child_doc = {
        "parent_id": ObjectId(parent_id),
        "username": username,
        "password_hash": hash_password(password),
        "name": name,
        "age": age,
        "alerts_consent": False,  # Default is OFF
        "has_seen_first_login_prompt": False,  # First-time login prompt not shown yet
        "pending_alert": {  # Per-incident permission tracking
            "exists": False,
            "bad_mood_count": 0,
            "created_at": None,
            "mood_id": None
        },
        "created_at": datetime.utcnow()
    }
    
    result = children_col.insert_one(child_doc)
    child_doc["_id"] = result.inserted_id
    
    logger.info(f"Created new child account: username={username}, id={result.inserted_id}, has_seen_first_login_prompt=False")
    
    return child_doc

def authenticate_child(username: str, password: str) -> Optional[dict]:
    """
    Authenticate a child with username and password
    
    Args:
        username: Child username
        password: Plain text password
        
    Returns:
        Child document if authentication successful, None otherwise
    """
    child = children_col.find_one({"username": username})
    
    if not child:
        return None
    
    if not verify_password(password, child["password_hash"]):
        return None
    
    return child

def get_child_by_id(child_id: str) -> Optional[dict]:
    """
    Get child by ID
    
    Args:
        child_id: Child ObjectId as string
        
    Returns:
        Child document or None
    """
    if not ObjectId.is_valid(child_id):
        return None
    
    return children_col.find_one({"_id": ObjectId(child_id)})

def update_child_consent(child_id: str, alerts_consent: bool) -> bool:
    """
    Update child's alert consent setting
    
    Args:
        child_id: Child ObjectId as string
        alerts_consent: New consent value
        
    Returns:
        True if update successful, False otherwise
    """
    if not ObjectId.is_valid(child_id):
        return False
    
    result = children_col.update_one(
        {"_id": ObjectId(child_id)},
        {"$set": {"alerts_consent": alerts_consent}}
    )
    
    return result.modified_count > 0

def verify_child_belongs_to_parent(child_id: str, parent_id: str) -> bool:
    """
    Verify that a child belongs to a specific parent
    
    Args:
        child_id: Child ObjectId as string
        parent_id: Parent ObjectId as string
        
    Returns:
        True if child belongs to parent, False otherwise
    """
    if not ObjectId.is_valid(child_id) or not ObjectId.is_valid(parent_id):
        return False
    
    child = children_col.find_one({
        "_id": ObjectId(child_id),
        "parent_id": ObjectId(parent_id)
    })
    
    return child is not None

def set_pending_alert(child_id: str, bad_mood_count: int, mood_id: ObjectId) -> bool:
    """
    Set pending alert for child (permission needed before sending email)
    
    Args:
        child_id: Child ObjectId as string
        bad_mood_count: Number of bad moods in last 7 days
        mood_id: The mood ObjectId that triggered the alert
        
    Returns:
        True if update successful, False otherwise
    """
    if not ObjectId.is_valid(child_id):
        return False
    
    result = children_col.update_one(
        {"_id": ObjectId(child_id)},
        {"$set": {
            "pending_alert.exists": True,
            "pending_alert.bad_mood_count": bad_mood_count,
            "pending_alert.created_at": datetime.utcnow(),
            "pending_alert.mood_id": mood_id
        }}
    )
    
    return result.modified_count > 0

def clear_pending_alert(child_id: str) -> bool:
    """
    Clear pending alert for child
    
    Args:
        child_id: Child ObjectId as string
        
    Returns:
        True if update successful, False otherwise
    """
    if not ObjectId.is_valid(child_id):
        return False
    
    result = children_col.update_one(
        {"_id": ObjectId(child_id)},
        {"$set": {
            "pending_alert.exists": False,
            "pending_alert.bad_mood_count": 0,
            "pending_alert.created_at": None,
            "pending_alert.mood_id": None
        }}
    )
    
    return result.modified_count > 0


def update_first_login_prompt_seen(child_id: str, seen: bool) -> bool:
    """
    Update first login prompt seen status for child
    
    Args:
        child_id: Child ObjectId as string
        seen: Whether the prompt has been seen
        
    Returns:
        True if update successful, False otherwise
    """
    if not ObjectId.is_valid(child_id):
        logger.error(f"Invalid child_id format: {child_id}")
        return False
    
    logger.debug(f"Updating has_seen_first_login_prompt for child {child_id} to {seen}")
    
    result = children_col.update_one(
        {"_id": ObjectId(child_id)},
        {"$set": {"has_seen_first_login_prompt": seen}}
    )
    
    logger.info(f"MongoDB update result for child {child_id}: matched={result.matched_count}, modified={result.modified_count}")
    
    if result.matched_count == 0:
        logger.error(f"No child document found with _id={child_id}")
        return False
    
    if result.modified_count == 0:
        logger.warning(f"Child {child_id} document matched but not modified (value may already be {seen})")
        # Still return True if document was found, even if value didn't change
        return True
    
    return True


def update_child_password(child_id: str, new_password: str) -> bool:
    """
    Update child's password
    
    Args:
        child_id: Child ObjectId as string
        new_password: New plain text password to hash and store
        
    Returns:
        True if update successful, False otherwise
    """
    if not ObjectId.is_valid(child_id):
        logger.error(f"Invalid child_id format: {child_id}")
        return False
    
    result = children_col.update_one(
        {"_id": ObjectId(child_id)},
        {"$set": {"password_hash": hash_password(new_password)}}
    )
    
    if result.modified_count > 0:
        logger.info(f"Password updated successfully for child {child_id}")
        return True
    else:
        logger.error(f"Failed to update password for child {child_id}")
        return False
