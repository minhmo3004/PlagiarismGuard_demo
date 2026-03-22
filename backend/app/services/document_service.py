from typing import Optional
from sqlalchemy.orm import Session
from app.db import models
import hashlib


class DocumentService:
    """
    Dịch vụ xử lý tài liệu (Document) trong cơ sở dữ liệu
    """

    @staticmethod
    def create_document(
        db: Session,
        owner_id: Optional[str],
        original_filename: str,
        s3_path: str,
        file_hash: str,
        file_size: int
    ):
        """
        Tạo một bản ghi tài liệu mới trong database
        
        Args:
            db: Phiên làm việc SQLAlchemy
            owner_id: ID của người sở hữu (có thể None)
            original_filename: Tên file gốc người dùng upload
            s3_path: Đường dẫn lưu trữ trên S3
            file_hash: Chuỗi hash SHA256 của nội dung file
            file_size: Kích thước file tính bằng byte
        
        Returns:
            Đối tượng Document vừa được tạo
        """
        doc = models.Document(
            owner_id=owner_id,
            original_filename=original_filename,
            s3_path=s3_path,
            file_hash_sha256=file_hash,
            file_size_bytes=file_size,
            status='processing'  # Trạng thái ban đầu: đang xử lý
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def update_extracted_text(
        db: Session,
        doc_id: str,
        text: str,
        word_count: int,
        page_count: Optional[int],
        extraction_method: Optional[str]
    ):
        """
        Cập nhật nội dung văn bản đã trích xuất từ tài liệu
        
        Args:
            db: Phiên làm việc SQLAlchemy
            doc_id: ID của tài liệu cần cập nhật
            text: Toàn bộ văn bản đã trích xuất
            word_count: Số từ trong văn bản
            page_count: Số trang (nếu có, tùy định dạng file)
            extraction_method: Phương pháp trích xuất (ví dụ: 'pdfplumber', 'tesseract', ...)
        
        Returns:
            Đối tượng Document đã cập nhật hoặc None nếu không tìm thấy
        """
        doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
        if not doc:
            return None
        
        doc.extracted_text = text
        doc.word_count = word_count
        doc.page_count = page_count
        doc.extraction_method = extraction_method
        doc.status = 'indexed'  # Chuyển trạng thái sang đã lập chỉ mục
        
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def get_document(db: Session, doc_id: str):
        """
        Lấy thông tin một tài liệu theo ID
        
        Args:
            db: Phiên làm việc SQLAlchemy
            doc_id: ID của tài liệu
        
        Returns:
            Đối tượng Document hoặc None nếu không tìm thấy
        """
        return db.query(models.Document).filter(models.Document.id == doc_id).first()

    @staticmethod
    def compute_sha256(data: bytes) -> str:
        """
        Tính giá trị hash SHA-256 của dữ liệu bytes
        
        Args:
            data: Nội dung file dưới dạng bytes
        
        Returns:
            Chuỗi hexdigest 64 ký tự của SHA-256
        """
        h = hashlib.sha256()
        h.update(data)
        return h.hexdigest()