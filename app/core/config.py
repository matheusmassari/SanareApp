from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
import os


class Settings(BaseSettings):
    """
    Application settings using Pydantic BaseSettings
    """
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "SanareApp"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database - Using environment variables with secure defaults
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "sanare_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "sanare_db")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # JWT - Must be provided via environment variables
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    ALGORITHM: str = "HS256"
    
    # CORS
    BACKEND_CORS_ORIGINS: str = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
    
    def get_cors_origins(self) -> List[str]:
        """Convert CORS origins string to list"""
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
        return self.BACKEND_CORS_ORIGINS
    
    @field_validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if not v:
            raise ValueError("SECRET_KEY must be provided via environment variable")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @field_validator('DATABASE_URL')
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL must be provided via environment variable")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Create global settings instance
settings = Settings() 