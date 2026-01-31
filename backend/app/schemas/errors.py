"""
Standardized Error Schemas for PriceSense API
All errors follow a consistent format for frontend consumption
"""
from pydantic import BaseModel, Field
from typing import Any, Optional
from enum import Enum


class ErrorCode(str, Enum):
    """Standardized error codes"""
    # Auth errors
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    USER_EXISTS = "USER_EXISTS"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    
    # Profile errors
    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"
    PROFILE_INVALID = "PROFILE_INVALID"
    
    # Financial errors
    HIGH_RISK = "HIGH_RISK"
    DTI_TOO_HIGH = "DTI_TOO_HIGH"
    INSUFFICIENT_EMERGENCY_FUND = "INSUFFICIENT_EMERGENCY_FUND"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    
    # Search errors
    SEARCH_FAILED = "SEARCH_FAILED"
    NO_RESULTS = "NO_RESULTS"
    INVALID_QUERY = "INVALID_QUERY"
    
    # Agent errors
    AGENT_TIMEOUT = "AGENT_TIMEOUT"
    AGENT_FAILED = "AGENT_FAILED"
    TRACE_NOT_FOUND = "TRACE_NOT_FOUND"
    
    # Rate limiting
    RATE_LIMITED = "RATE_LIMITED"
    
    # General
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class ErrorResponse(BaseModel):
    """Standard error response format"""
    error_code: ErrorCode
    message: str
    details: Optional[dict[str, Any]] = Field(default_factory=dict)
    trace_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "HIGH_RISK",
                "message": "This purchase exceeds safe spending limits",
                "details": {
                    "dti_ratio": 0.45,
                    "max_allowed": 0.36
                },
                "trace_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class ValidationErrorDetail(BaseModel):
    """Validation error detail for field-level errors"""
    field: str
    message: str
    type: str


class ValidationErrorResponse(BaseModel):
    """Validation error response with field details"""
    error_code: ErrorCode = ErrorCode.VALIDATION_ERROR
    message: str = "Validation failed"
    details: list[ValidationErrorDetail]
