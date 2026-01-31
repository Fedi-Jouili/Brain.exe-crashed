"""
Security Middleware
JWT verification, rate limiting, and request context injection
"""
from typing import Optional, Callable
from datetime import datetime, timezone
import time
import uuid

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.security import (
    verify_access_token, 
    hash_token_for_storage, 
    TokenBlacklist
)
from app.schemas.auth import AuthenticatedUser, UserRole
from app.schemas.errors import ErrorCode, ErrorResponse
from app.core.config import settings


# HTTP Bearer scheme
security = HTTPBearer(auto_error=False)


class RateLimiter:
    """
    Simple in-memory rate limiter
    In production, use Redis-based rate limiting
    """
    _requests: dict[str, list[float]] = {}
    
    @classmethod
    def is_allowed(cls, key: str, limit: int, window_seconds: int = 60) -> bool:
        """Check if request is within rate limit"""
        now = time.time()
        
        if key not in cls._requests:
            cls._requests[key] = []
        
        # Remove old requests outside window
        cls._requests[key] = [
            ts for ts in cls._requests[key] 
            if now - ts < window_seconds
        ]
        
        if len(cls._requests[key]) >= limit:
            return False
        
        cls._requests[key].append(now)
        return True
    
    @classmethod
    def get_remaining(cls, key: str, limit: int, window_seconds: int = 60) -> int:
        """Get remaining requests in window"""
        now = time.time()
        
        if key not in cls._requests:
            return limit
        
        valid_requests = [
            ts for ts in cls._requests[key] 
            if now - ts < window_seconds
        ]
        
        return max(0, limit - len(valid_requests))


async def get_current_user(request: Request) -> Optional[AuthenticatedUser]:
    """
    Extract and validate user from request
    Returns None if no valid token present
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    
    # Check blacklist
    token_hash = hash_token_for_storage(token)
    if TokenBlacklist.is_blacklisted(token_hash):
        return None
    
    # Verify token
    payload = verify_access_token(token)
    if not payload:
        return None
    
    return AuthenticatedUser(
        user_id=payload.sub,
        role=payload.role,
        session_id=payload.session_id
    )


async def require_auth(request: Request) -> AuthenticatedUser:
    """
    Dependency that requires authentication
    Raises 401 if not authenticated
    """
    user = await get_current_user(request)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code=ErrorCode.UNAUTHORIZED,
                message="Authentication required"
            ).model_dump()
        )
    
    return user


async def require_admin(request: Request) -> AuthenticatedUser:
    """
    Dependency that requires admin role
    Raises 403 if not admin
    """
    user = await require_auth(request)
    
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorResponse(
                error_code=ErrorCode.FORBIDDEN,
                message="Admin access required"
            ).model_dump()
        )
    
    return user


def rate_limit(limit: int, window_seconds: int = 60):
    """
    Rate limiting dependency factory
    """
    async def rate_limit_dependency(request: Request):
        # Use IP + user_id as key
        client_ip = request.client.host if request.client else "unknown"
        user = await get_current_user(request)
        user_id = user.user_id if user else "anonymous"
        
        key = f"{client_ip}:{user_id}:{request.url.path}"
        
        if not RateLimiter.is_allowed(key, limit, window_seconds):
            remaining = RateLimiter.get_remaining(key, limit, window_seconds)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=ErrorResponse(
                    error_code=ErrorCode.RATE_LIMITED,
                    message="Rate limit exceeded",
                    details={
                        "limit": limit,
                        "window_seconds": window_seconds,
                        "remaining": remaining
                    }
                ).model_dump(),
                headers={"Retry-After": str(window_seconds)}
            )
    
    return rate_limit_dependency


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to inject request context (request_id, timing)
    """
    async def dispatch(self, request: Request, call_next: Callable):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{(time.time() - request.state.start_time) * 1000:.2f}ms"
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    """
    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
