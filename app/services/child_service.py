"""
Child Service
Business logic for child operations
"""
from datetime import datetime
from typing import Optional
from bson import ObjectId
from fastapi import HTTPException, status
from app.database.db import children_col
from app.services.auth_service import hash_password, verify_password

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
        "created_at": datetime.utcnow()
    }
    
    result = children_col.insert_one(child_doc)
    child_doc["_id"] = result.inserted_id
    
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
