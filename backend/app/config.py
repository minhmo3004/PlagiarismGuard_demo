"""
Configuration module for PlagiarismGuard
Loads settings from environment variables
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "PlagiarismGuard"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # S3/MinIO
    S3_ENDPOINT: Optional[str] = None
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET: str = "plagiarism-files"
    S3_REGION: str = "us-east-1"
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024  # 20MB
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".docx", ".txt", ".tex"]
    
    # MinHash/LSH Parameters
    MINHASH_SEED: int = 42
    MINHASH_PERMUTATIONS: int = 128
    LSH_THRESHOLD: float = 0.4
    LSH_BANDS: int = 32
    LSH_ROWS: int = 4
    SHINGLE_SIZE: int = 7
    
    # OCR
    OCR_TIMEOUT_SECONDS: int = 300
    OCR_TIMEOUT_PER_PAGE: int = 30
    MAX_PAGES_FOR_OCR: int = 100
    
    # Rate Limiting
    RATE_LIMIT_FREE: str = "20/hour"
    RATE_LIMIT_PREMIUM: str = "100/hour"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
