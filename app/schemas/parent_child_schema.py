"""
Parent, Child, and Trusted Contact Schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# Child Management
class ChildCreateRequest(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    name: str
    age: int = Field(..., gt=0, lt=20)

class ChildResponse(BaseModel):
    id: str
    username: str
    name: str
    age: int
    alerts_consent: bool
    parent_id: str
    created_at: datetime

class ChildListResponse(BaseModel):
    id: str
    username: str
    name: str
    age: int
    alerts_consent: bool

class ChildProfileResponse(BaseModel):
    id: str
    username: str
    name: str
    age: int
    alerts_consent: bool

class ChildConsentUpdate(BaseModel):
    alerts_consent: bool

# Trusted Contacts
class TrustedContactInviteRequest(BaseModel):
    email: EmailStr
    relationship: str = Field(..., pattern="^(Teacher|Relative|Family Friend|Other)$")

class TrustedContactResponse(BaseModel):
    id: str
    email: str
    relationship: str
    status: str  # pending, accepted, or removed
    invited_at: datetime
    accepted_at: Optional[datetime] = None

class TrustedContactRemoveRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=500)

# Error Response
class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    details: Optional[dict] = None
