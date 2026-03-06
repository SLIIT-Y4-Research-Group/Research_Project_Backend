"""
Parent Service
Business logic for parent operations
"""
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from fastapi import HTTPException, status
from app.database.db import parents_col, children_col
from app.services.auth_service import hash_password, verify_password

def create_parent(email: str, password: str) -> dict:
    """
    Create a new parent account
    
    Args:
        email: Parent email (must be unique)
        password: Plain text password (will be hashed)
        
    Returns:
        Created parent document
        
    Raises:
        HTTPException: If email already exists or password too long
    """
    # Check if email already exists
    existing = parents_col.find_one({"email": email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Debug: Check what we're actually getting
    print(f"DEBUG - Type of password: {type(password)}")
    print(f"DEBUG - Password value: {password}")
    print(f"DEBUG - Password bytes length: {len(password.encode('utf-8'))}")
    
    # Validate password is a string
    if not isinstance(password, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be a string, received {type(password)}"
        )
    
    # Check password length (bcrypt limit is 72 bytes)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password too long (max 72 bytes). Your password is {len(password_bytes)} bytes."
        )
    
    # Hash the password
    try:
        password_hash = hash_password(password)
    except Exception as e:
        print(f"ERROR hashing password: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password hashing failed: {str(e)}"
        )
    
    # Create parent document
    parent_doc = {
        "email": email,
        "password_hash": password_hash,
        "created_at": datetime.utcnow()
    }
    
    result = parents_col.insert_one(parent_doc)
    parent_doc["_id"] = result.inserted_id
    
    return parent_doc

def authenticate_parent(email: str, password: str) -> Optional[dict]:
    """
    Authenticate a parent with email and password
    
    Args:
        email: Parent email
        password: Plain text password
        
    Returns:
        Parent document if authentication successful, None otherwise
    """
    parent = parents_col.find_one({"email": email})
    
    if not parent:
        return None
    
    if not verify_password(password, parent["password_hash"]):
        return None
    
    return parent

def get_parent_by_id(parent_id: str) -> Optional[dict]:
    """
    Get parent by ID
    
    Args:
        parent_id: Parent ObjectId as string
        
    Returns:
        Parent document or None
    """
    if not ObjectId.is_valid(parent_id):
        return None
    
    return parents_col.find_one({"_id": ObjectId(parent_id)})

def get_parent_children(parent_id: str) -> List[dict]:
    """
    Get all children for a parent
    
    Args:
        parent_id: Parent ObjectId as string
        
    Returns:
        List of child documents
    """
    if not ObjectId.is_valid(parent_id):
        return []
    
    children = children_col.find({"parent_id": ObjectId(parent_id)})
    return list(children)
