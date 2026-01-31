"""
Authentication Schemas
JWT-based auth with access/refresh token rotation
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum
import re


class UserRole(str, Enum):
    """User roles for authorization"""
    USER = "USER"
    ADMIN = "ADMIN"
    SYSTEM = "SYSTEM"


class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=2, max_length=100)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str  # user_id
    role: UserRole
    session_id: str
    exp: datetime
    iat: datetime
    type: str  # "access" or "refresh"


class TokenResponse(BaseModel):
    """Token response (access token in body, refresh in httpOnly cookie)"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshResponse(BaseModel):
    """Refresh token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User data response"""
    id: str
    email: str
    name: str
    role: UserRole
    created_at: datetime
    has_profile: bool
    
    class Config:
        from_attributes = True


class AuthenticatedUser(BaseModel):
    """Injected user context from middleware"""
    user_id: str
    role: UserRole
    session_id: str
    email: Optional[str] = None
