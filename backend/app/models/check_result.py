"""
Check result models
"""
from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional, List
from enum import Enum
from decimal import Decimal


class CheckStatus(str, Enum):
    """Check job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MatchSegment(BaseModel):
    """Matched segment in diff"""
    query_start: int
    query_end: int
    source_start: int
    source_end: int
    length: int
    query_text: str
    source_text: str


class MatchDetail(BaseModel):
    """Match detail for a single source document"""
    source_doc_id: UUID4
    source_doc_title: Optional[str]
    similarity_score: Decimal
    matched_segments: List[MatchSegment]


class CheckResultBase(BaseModel):
    """Base check result model"""
    query_filename: str


class CheckResultCreate(CheckResultBase):
    """Check result creation model"""
    user_id: UUID4
    query_doc_id: Optional[UUID4] = None


class CheckResultInDB(CheckResultBase):
    """Check result model in database"""
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
    """Check result model for API responses"""
    id: UUID4
    status: CheckStatus
    overall_similarity: Optional[Decimal]
    match_count: int
    processing_time_ms: Optional[int]
    created_at: datetime
    matches: Optional[List[MatchDetail]] = None

    class Config:
        from_attributes = True
