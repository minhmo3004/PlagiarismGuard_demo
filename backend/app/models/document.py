"""
Document models
"""
from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional
from enum import Enum


class DocumentStatus(str, Enum):
    """Document processing status"""
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class DocumentBase(BaseModel):
    """Base document model"""
    title: Optional[str] = None
    original_filename: str
    language: str = "vi"


class DocumentCreate(DocumentBase):
    """Document creation model"""
    s3_path: str
    file_hash_sha256: str
    file_size_bytes: int
    owner_id: Optional[UUID4] = None


class DocumentInDB(DocumentBase):
    """Document model in database"""
    id: UUID4
    owner_id: Optional[UUID4]
    s3_path: str
    file_hash_sha256: str
    file_size_bytes: int
    word_count: Optional[int]
    page_count: Optional[int]
    extraction_method: Optional[str]
    status: DocumentStatus
    error_message: Optional[str]
    created_at: datetime
    indexed_at: Optional[datetime]

    class Config:
        from_attributes = True


class Document(DocumentBase):
    """Document model for API responses"""
    id: UUID4
    status: DocumentStatus
    word_count: Optional[int]
    page_count: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
