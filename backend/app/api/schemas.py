"""
Các schema Pydantic dùng cho request/response của API
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# Schema liên quan đến xác thực (Auth)
class UserRegister(BaseModel):
    """Yêu cầu đăng ký người dùng"""
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """Yêu cầu đăng nhập"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Phản hồi chứa token"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Yêu cầu làm mới token"""
    refresh_token: str


# Schema liên quan đến kiểm tra đạo văn (Check)
class CheckUploadResponse(BaseModel):
    """Phản hồi sau khi tải file lên"""
    job_id: str
    status: str
    message: str


class JobStatus(BaseModel):
    """Phản hồi trạng thái công việc"""
    job_id: str
    status: str  # pending, processing, done, failed, cancelled
    progress: Optional[int] = None  # 0-100
    error: Optional[str] = None
    can_retry: bool = False
    created_at: datetime
    completed_at: Optional[datetime] = None


class MatchSegment(BaseModel):
    """Đoạn văn bản khớp (trong so sánh diff)"""
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
    """Chi tiết một tài liệu nguồn khớp"""
    source_doc_id: str
    source_doc_title: Optional[str]
    similarity_score: float
    segment_count: int
    segments: Optional[List[MatchSegment]] = None


class CheckResult(BaseModel):
    """Phản hồi kết quả kiểm tra đạo văn"""
    job_id: str
    status: str
    query_filename: str
    overall_similarity: Optional[float] = None
    match_count: int
    matches: List[MatchDetail]
    processing_time_ms: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# Schema xử lý lỗi
class ErrorDetail(BaseModel):
    """Chi tiết lỗi"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    retry_after: Optional[int] = None


class ErrorResponse(BaseModel):
    """Phản hồi lỗi chuẩn"""
    error: ErrorDetail