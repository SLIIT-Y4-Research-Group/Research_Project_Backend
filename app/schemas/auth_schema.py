"""
Authentication Schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Parent Auth
class ParentRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

class ParentLoginRequest(BaseModel):
    email: EmailStr
    password: str

# Child Auth
class ChildLoginRequest(BaseModel):
    username: str
    password: str

# Token Response
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    parent: Optional[dict] = None
    child: Optional[dict] = None

# Token Data (for JWT payload)
class TokenData(BaseModel):
    id: str
    role: str  # "parent" or "child"
    email: Optional[str] = None
    username: Optional[str] = None
