"""
Các model Pydantic dùng cho kết quả kiểm tra đạo văn (check result)
Bao gồm: trạng thái công việc, đoạn khớp, chi tiết khớp, và các model response/create
"""
from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional, List
from enum import Enum
from decimal import Decimal


class CheckStatus(str, Enum):
    """Trạng thái công việc kiểm tra đạo văn"""
    PENDING = "pending"      # Đang chờ xử lý
    PROCESSING = "processing"  # Đang xử lý
    DONE = "done"            # Hoàn tất
    FAILED = "failed"        # Thất bại
    CANCELLED = "cancelled"  # Đã hủy


class MatchSegment(BaseModel):
    """Một đoạn văn bản khớp giữa tài liệu query và tài liệu nguồn"""
    query_start: int
    query_end: int
    source_start: int
    source_end: int
    length: int
    query_text: str
    source_text: str


class MatchDetail(BaseModel):
    """Chi tiết khớp với một tài liệu nguồn cụ thể"""
    source_doc_id: UUID4
    source_doc_title: Optional[str]
    similarity_score: Decimal
    matched_segments: List[MatchSegment]


class CheckResultBase(BaseModel):
    """Model cơ sở cho kết quả kiểm tra"""
    query_filename: str


class CheckResultCreate(CheckResultBase):
    """Model dùng để tạo mới bản ghi kết quả kiểm tra"""
    user_id: UUID4
    query_doc_id: Optional[UUID4] = None


class CheckResultInDB(CheckResultBase):
    """Model đại diện cho bản ghi kết quả kiểm tra trong cơ sở dữ liệu"""
    id: UUID4
    user_id: UUID4
    query_doc_id: Optional[UUID4]
    overall_similarity: Optional[Decimal]
    match_count: int
    status: CheckStatus
    error_message: Optional[str]
    processing_time_ms: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class CheckResult(CheckResultBase):
    """Model dùng cho phản hồi API (response)"""
    id: UUID4
    status: CheckStatus
    overall_similarity: Optional[Decimal]
    match_count: int
    processing_time_ms: Optional[int]
    created_at: datetime
    matches: Optional[List[MatchDetail]] = None

    class Config:
        from_attributes = True