"""
Module cấu hình cho PlagiarismGuard
Tải các thiết lập từ biến môi trường (.env)
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Cấu hình ứng dụng"""
    
    # Thông tin ứng dụng
    APP_NAME: str = "PlagiarismGuard"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Bảo mật
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
    
    # Cấu hình MinIO / S3
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_UPLOADS: str = "plagiarism-uploads"
    MINIO_BUCKET_CORPUS: str = "plagiarism-corpus"
    MINIO_SECURE: bool = False
    
    # Giới hạn tải file lên
    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024  # 20MB
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".docx", ".txt", ".tex"]
    
    # Tham số MinHash / LSH
    MINHASH_SEED: int = 42
    MINHASH_PERMUTATIONS: int = 128
    LSH_THRESHOLD: float = 0.3   # Đã giảm từ 0.4 để tăng khả năng phát hiện
    LSH_BANDS: int = 16
    LSH_ROWS: int = 8
    SHINGLE_SIZE: int = 7
    
    # Cấu hình OCR
    OCR_TIMEOUT: int = 30        # đơn vị giây
    TESSERACT_LANG: str = "vie+eng"
    MAX_PAGES_FOR_OCR: int = 100
    
    # Giới hạn tốc độ (Rate Limiting)
    RATE_LIMIT_PER_MINUTE: str = "20/hour"
    RATE_LIMIT_PREMIUM: str = "100/hour"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instance settings toàn cục
settings = Settings()