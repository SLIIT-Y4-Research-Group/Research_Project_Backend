"""
Authentication Service
Handles password hashing, JWT creation, and token validation
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES
from app.schemas.auth_schema import TokenData
from bson import ObjectId

# Debug: Check bcrypt module location
try:
    import bcrypt
    print("=" * 60)
    print("BCRYPT MODULE INFO:")
    print(f"  Location: {bcrypt.__file__}")
    print(f"  Version: {getattr(bcrypt, '__version__', 'unknown')}")
    print("=" * 60)
except Exception as e:
    print(f"WARNING: Could not load bcrypt module: {e}")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token security
security = HTTPBearer()

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    # Ensure we're working with a plain string
    if not isinstance(password, str):
        raise ValueError(f"Password must be a string, got {type(password)}")
    
    # Ensure password is not too long
    if len(password.encode('utf-8')) > 72:
        raise ValueError("Password cannot be longer than 72 bytes")
    
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Dictionary with user data (should include 'id' and 'role')
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return encoded_jwt

def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData object
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("id")
        role: str = payload.get("role")
        
        if user_id is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing required fields"
            )
        
        token_data = TokenData(
            id=user_id,
            role=role,
            email=payload.get("email"),
            username=payload.get("username")
        )
        return token_data
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """
    Dependency to get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        TokenData object with user information
    """
    token = credentials.credentials
    return decode_token(token)

def get_current_parent(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """
    Dependency to ensure current user is a parent
    
    Args:
        current_user: Current user token data
        
    Returns:
        TokenData if user is a parent
        
    Raises:
        HTTPException: If user is not a parent
    """
    if current_user.role != "parent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Parent role required"
        )
    return current_user

def get_current_child(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """
    Dependency to ensure current user is a child
    
    Args:
        current_user: Current user token data
        
    Returns:
        TokenData if user is a child
        
    Raises:
        HTTPException: If user is not a child
    """
    if current_user.role != "child":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Child role required"
        )
    return current_user
