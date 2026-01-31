"""
Security Module
JWT token management, password hashing, and token rotation
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import secrets
import hashlib

from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.auth import TokenPayload, UserRole


# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def generate_session_id() -> str:
    """Generate unique session ID for token tracking"""
    return secrets.token_urlsafe(32)


def create_access_token(
    user_id: str,
    role: UserRole,
    session_id: str,
    expires_delta: Optional[timedelta] = None
) -> Tuple[str, datetime]:
    """
    Create JWT access token
    Returns: (token, expiry_datetime)
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    
    payload = {
        "sub": user_id,
        "role": role.value,
        "session_id": session_id,
        "exp": expire,
        "iat": now,
        "type": "access"
    }
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, expire


def create_refresh_token(
    user_id: str,
    role: UserRole,
    session_id: str,
    expires_delta: Optional[timedelta] = None
) -> Tuple[str, datetime]:
    """
    Create JWT refresh token (longer lived)
    Returns: (token, expiry_datetime)
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    
    payload = {
        "sub": user_id,
        "role": role.value,
        "session_id": session_id,
        "exp": expire,
        "iat": now,
        "type": "refresh"
    }
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, expire


def decode_token(token: str) -> Optional[TokenPayload]:
    """
    Decode and validate JWT token
    Returns TokenPayload if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        return TokenPayload(
            sub=payload["sub"],
            role=UserRole(payload["role"]),
            session_id=payload["session_id"],
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            type=payload["type"]
        )
    except (JWTError, ValidationError, KeyError):
        return None


def verify_access_token(token: str) -> Optional[TokenPayload]:
    """Verify access token specifically"""
    payload = decode_token(token)
    if payload and payload.type == "access":
        return payload
    return None


def verify_refresh_token(token: str) -> Optional[TokenPayload]:
    """Verify refresh token specifically"""
    payload = decode_token(token)
    if payload and payload.type == "refresh":
        return payload
    return None


def hash_token_for_storage(token: str) -> str:
    """
    Hash token for storage (for refresh token revocation tracking)
    We don't store raw tokens, only hashes
    """
    return hashlib.sha256(token.encode()).hexdigest()


class TokenBlacklist:
    """
    Token blacklist for revocation
    In production, this should use Redis
    """
    _blacklist: set[str] = set()
    
    @classmethod
    def add(cls, token_hash: str) -> None:
        """Add token hash to blacklist"""
        cls._blacklist.add(token_hash)
    
    @classmethod
    def is_blacklisted(cls, token_hash: str) -> bool:
        """Check if token is blacklisted"""
        return token_hash in cls._blacklist
    
    @classmethod
    def clear_expired(cls) -> None:
        """Clear expired tokens (should be called periodically)"""
        # In production, use Redis with TTL
        pass
