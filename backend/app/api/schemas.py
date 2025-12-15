"""
Pydantic schemas for API requests/responses
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# Auth schemas
class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Token refresh request"""
    refresh_token: str


# Check schemas
class CheckUploadResponse(BaseModel):
    """Upload response"""
    job_id: str
    status: str
    message: str


class JobStatus(BaseModel):
    """Job status response"""
    job_id: str
    status: str  # pending, processing, done, failed, cancelled
    progress: Optional[int] = None  # 0-100
    error: Optional[str] = None
    can_retry: bool = False
    created_at: datetime
    completed_at: Optional[datetime] = None


class MatchSegment(BaseModel):
    """Matched segment in diff"""
    query_start: int
    query_end: int
    source_start: int
    source_end: int
    length: int
    query_text: str
    source_text: str
    query_text_truncated: bool = False
    source_text_truncated: bool = False


class MatchDetail(BaseModel):
    """Match detail for a source document"""
    source_doc_id: str
    source_doc_title: Optional[str]
    similarity_score: float
    segment_count: int
    segments: Optional[List[MatchSegment]] = None


class CheckResult(BaseModel):
    """Check result response"""
    job_id: str
    status: str
    query_filename: str
    overall_similarity: Optional[float] = None
    match_count: int
    matches: List[MatchDetail]
    processing_time_ms: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# Error schema
class ErrorDetail(BaseModel):
    """Error detail"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    retry_after: Optional[int] = None


class ErrorResponse(BaseModel):
    """Error response"""
    error: ErrorDetail
