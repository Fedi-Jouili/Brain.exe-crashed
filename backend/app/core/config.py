"""
PriceSense Backend Configuration
Environment-based configuration with validation
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App
    APP_NAME: str = "PriceSense API"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    
    # Security
    SECRET_KEY: str = Field(..., description="JWT secret key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = Field(default="postgresql://localhost/pricesense")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    
    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "products"
    
    # Rate Limiting
    RATE_LIMIT_LOGIN: int = 5  # attempts per minute
    RATE_LIMIT_SEARCH: int = 30  # requests per minute
    RATE_LIMIT_GENERAL: int = 100  # requests per minute
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "https://pricesense.app"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


settings = get_settings()
