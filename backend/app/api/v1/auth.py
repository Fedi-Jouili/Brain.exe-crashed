"""
Authentication Routes
JWT-based auth with access/refresh token rotation
"""
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, status, Request
from fastapi.security import HTTPBearer

from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    generate_session_id,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    hash_token_for_storage,
    TokenBlacklist
)
from app.core.middleware import require_auth, rate_limit, RateLimiter
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshResponse,
    UserResponse,
    AuthenticatedUser,
    UserRole
)
from app.schemas.errors import ErrorCode, ErrorResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory user store (replace with database in production)
# Structure: {email: {id, email, name, password_hash, role, created_at, has_profile}}
_users_db: dict = {}
_sessions_db: dict = {}  # {session_id: {user_id, refresh_token_hash, created_at}}


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        409: {"model": ErrorResponse, "description": "User already exists"}
    }
)
async def register(
    request: RegisterRequest,
    response: Response,
    _: Annotated[None, Depends(rate_limit(10, 60))]  # 10 registrations per minute
):
    """
    Register a new user account.
    
    Returns access token in response body and sets refresh token as httpOnly cookie.
    """
    # Check if user exists
    if request.email.lower() in _users_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                error_code=ErrorCode.USER_EXISTS,
                message="A user with this email already exists"
            ).model_dump()
        )
    
    # Create user
    import uuid
    from datetime import datetime, timezone
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": request.email.lower(),
        "name": request.name,
        "password_hash": hash_password(request.password),
        "role": UserRole.USER,
        "created_at": datetime.now(timezone.utc),
        "has_profile": False
    }
    _users_db[request.email.lower()] = user
    
    # Generate tokens
    session_id = generate_session_id()
    access_token, access_exp = create_access_token(user_id, UserRole.USER, session_id)
    refresh_token, refresh_exp = create_refresh_token(user_id, UserRole.USER, session_id)
    
    # Store session
    _sessions_db[session_id] = {
        "user_id": user_id,
        "refresh_token_hash": hash_token_for_storage(refresh_token),
        "created_at": datetime.now(timezone.utc)
    }
    
    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        429: {"model": ErrorResponse, "description": "Rate limited"}
    }
)
async def login(
    request: LoginRequest,
    response: Response,
    _: Annotated[None, Depends(rate_limit(settings.RATE_LIMIT_LOGIN, 60))]
):
    """
    Authenticate user and return tokens.
    
    Returns access token in response body and sets refresh token as httpOnly cookie.
    """
    from datetime import datetime, timezone
    
    # Find user
    user = _users_db.get(request.email.lower())
    
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code=ErrorCode.INVALID_CREDENTIALS,
                message="Invalid email or password"
            ).model_dump()
        )
    
    # Generate tokens
    session_id = generate_session_id()
    access_token, access_exp = create_access_token(user["id"], user["role"], session_id)
    refresh_token, refresh_exp = create_refresh_token(user["id"], user["role"], session_id)
    
    # Store session
    _sessions_db[session_id] = {
        "user_id": user["id"],
        "refresh_token_hash": hash_token_for_storage(refresh_token),
        "created_at": datetime.now(timezone.utc)
    }
    
    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired refresh token"}
    }
)
async def refresh_token(
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None
):
    """
    Refresh access token using refresh token from cookie.
    
    Implements token rotation: old refresh token is invalidated and new one issued.
    """
    from datetime import datetime, timezone
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code=ErrorCode.TOKEN_INVALID,
                message="No refresh token provided"
            ).model_dump()
        )
    
    # Verify refresh token
    payload = verify_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code=ErrorCode.TOKEN_EXPIRED,
                message="Refresh token is invalid or expired"
            ).model_dump()
        )
    
    # Check if token is revoked
    token_hash = hash_token_for_storage(refresh_token)
    if TokenBlacklist.is_blacklisted(token_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code=ErrorCode.TOKEN_REVOKED,
                message="Refresh token has been revoked"
            ).model_dump()
        )
    
    # Verify session exists
    session = _sessions_db.get(payload.session_id)
    if not session or session["refresh_token_hash"] != token_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code=ErrorCode.TOKEN_INVALID,
                message="Session not found or token mismatch"
            ).model_dump()
        )
    
    # Blacklist old refresh token
    TokenBlacklist.add(token_hash)
    
    # Generate new tokens (token rotation)
    new_session_id = generate_session_id()
    new_access_token, _ = create_access_token(payload.sub, payload.role, new_session_id)
    new_refresh_token, _ = create_refresh_token(payload.sub, payload.role, new_session_id)
    
    # Update session
    del _sessions_db[payload.session_id]
    _sessions_db[new_session_id] = {
        "user_id": payload.sub,
        "refresh_token_hash": hash_token_for_storage(new_refresh_token),
        "created_at": datetime.now(timezone.utc)
    }
    
    # Set new refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    
    return RefreshResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"}
    }
)
async def logout(
    response: Response,
    current_user: Annotated[AuthenticatedUser, Depends(require_auth)],
    refresh_token: Annotated[str | None, Cookie()] = None
):
    """
    Logout user by revoking tokens and clearing session.
    """
    # Revoke refresh token if present
    if refresh_token:
        TokenBlacklist.add(hash_token_for_storage(refresh_token))
    
    # Delete session
    if current_user.session_id in _sessions_db:
        del _sessions_db[current_user.session_id]
    
    # Clear cookie
    response.delete_cookie("refresh_token")
    
    return None


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"}
    }
)
async def get_current_user_info(
    current_user: Annotated[AuthenticatedUser, Depends(require_auth)]
):
    """
    Get current authenticated user's information.
    """
    # Find user by ID
    for user in _users_db.values():
        if user["id"] == current_user.user_id:
            return UserResponse(
                id=user["id"],
                email=user["email"],
                name=user["name"],
                role=user["role"],
                created_at=user["created_at"],
                has_profile=user["has_profile"]
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ErrorResponse(
            error_code=ErrorCode.USER_NOT_FOUND,
            message="User not found"
        ).model_dump()
    )


# Export users_db for profile router
def get_users_db():
    return _users_db
