"""
Các model Pydantic dùng cho tài liệu (document)
Bao gồm: trạng thái xử lý tài liệu, model cơ sở, tạo mới, lưu trong DB và phản hồi API
"""
from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional
from enum import Enum


class DocumentStatus(str, Enum):
    """Trạng thái xử lý của tài liệu"""
    PROCESSING = "processing"   # Đang xử lý (trích xuất văn bản, lập chỉ mục, v.v.)
    INDEXED = "indexed"         # Đã hoàn tất lập chỉ mục (có thể dùng để so sánh)
    FAILED = "failed"           # Xử lý thất bại


class DocumentBase(BaseModel):
    """Model cơ sở cho thông tin tài liệu"""
    title: Optional[str] = None
    original_filename: str
    language: str = "vi"        # Mặc định là tiếng Việt


class DocumentCreate(DocumentBase):
    """Model dùng để tạo mới bản ghi tài liệu"""
    s3_path: str
    file_hash_sha256: str
    file_size_bytes: int
    owner_id: Optional[UUID4] = None


class DocumentInDB(DocumentBase):
    """Model đại diện cho bản ghi tài liệu trong cơ sở dữ liệu"""
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
    """Model dùng cho phản hồi API (response)"""
    id: UUID4
    status: DocumentStatus
    word_count: Optional[int]
    page_count: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True