"""
Các model SQLAlchemy đại diện cho bảng trong cơ sở dữ liệu
Bao gồm: User, Document, CheckResult, MatchDetail
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, BigInteger, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .database import Base


class User(Base):
    """Bảng người dùng (users)"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    tier = Column(String(20), default='free')  # free, premium, enterprise, admin
    daily_uploads = Column(Integer, default=0)
    daily_checks = Column(Integer, default=0)
    last_reset_date = Column(DateTime, server_default=func.current_date())
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Document(Base):
    """Bảng tài liệu (documents) - cả tài liệu người dùng upload và corpus"""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    title = Column(String(500))
    original_filename = Column(String(255))
    s3_path = Column(String(500), nullable=True)  # đường dẫn MinIO/S3, nullable cho tài liệu corpus
    file_hash_sha256 = Column(String(64), unique=True, nullable=False)
    file_size_bytes = Column(BigInteger)
    word_count = Column(Integer)
    page_count = Column(Integer)
    language = Column(String(10), default='vi')
    extraction_method = Column(String(50))
    status = Column(String(20), default='processing')  # processing, completed, failed
    error_message = Column(Text)
    extracted_text = Column(Text)  # văn bản đã trích xuất từ file, lưu trực tiếp trong DB
    
    # Metadata dành cho tài liệu trong corpus
    author = Column(String(255), nullable=True)
    university = Column(String(255), nullable=True)
    year = Column(Integer, nullable=True)
    topic = Column(String(255), nullable=True)
    is_corpus = Column(Integer, default=0)  # 1 = tài liệu corpus, 0 = tài liệu người dùng upload
    
    created_at = Column(DateTime, server_default=func.now())
    indexed_at = Column(DateTime)  # thời điểm hoàn tất lập chỉ mục (indexing) cho corpus

    owner = relationship('User')


class CheckResult(Base):
    """Bảng kết quả kiểm tra đạo văn (check_results)"""
    __tablename__ = "check_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    query_doc_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'), nullable=True)
    query_filename = Column(String(255))
    overall_similarity = Column(Numeric(5, 4))  # giá trị từ 0.0000 đến 1.0000
    plagiarism_level = Column(String(20))  # none, low, medium, high
    match_count = Column(Integer, default=0)
    word_count = Column(Integer)
    status = Column(String(20), default='pending')  # pending, processing, completed, failed, cancelled
    error_message = Column(Text)
    processing_time_ms = Column(Integer)
    file_path = Column(String(1000))  # object key trong MinIO cho file upload
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)

    user = relationship('User')
    document = relationship('Document')
    match_details = relationship('MatchDetail', back_populates='result', cascade='all, delete-orphan')


class MatchDetail(Base):
    """Chi tiết từng match giữa tài liệu query và tài liệu nguồn trong corpus"""
    __tablename__ = "match_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_id = Column(UUID(as_uuid=True), ForeignKey('check_results.id', ondelete='CASCADE'))
    source_doc_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'))
    similarity_score = Column(Numeric(5, 4))
    
    # Chi tiết các đoạn văn bản trùng khớp (lưu dưới dạng JSON array dạng text)
    # Format ví dụ: 
    # [{"query_text": "...", "query_start": 0, "query_end": 100, 
    #   "source_text": "...", "source_start": 50, "source_end": 150}]
    matched_segments = Column(Text)
    
    # Metadata của tài liệu nguồn (để hiển thị trên frontend mà không cần join thêm)
    source_title = Column(String(500))
    source_author = Column(String(255))
    source_university = Column(String(255))
    source_year = Column(Integer)
    
    created_at = Column(DateTime, server_default=func.now())

    result = relationship('CheckResult', back_populates='match_details')
    source_doc = relationship('Document')