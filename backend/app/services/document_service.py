from typing import Optional
from sqlalchemy.orm import Session
from app.db import models
import hashlib


class DocumentService:
    @staticmethod
    def create_document(db: Session, owner_id: Optional[str], original_filename: str, s3_path: str, file_hash: str, file_size: int):
        doc = models.Document(
            owner_id=owner_id,
            original_filename=original_filename,
            s3_path=s3_path,
            file_hash_sha256=file_hash,
            file_size_bytes=file_size,
            status='processing'
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def update_extracted_text(db: Session, doc_id: str, text: str, word_count: int, page_count: Optional[int], extraction_method: Optional[str]):
        doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
        if not doc:
            return None
        doc.extracted_text = text
        doc.word_count = word_count
        doc.page_count = page_count
        doc.extraction_method = extraction_method
        doc.status = 'indexed'
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def get_document(db: Session, doc_id: str):
        return db.query(models.Document).filter(models.Document.id == doc_id).first()

    @staticmethod
    def compute_sha256(data: bytes) -> str:
        h = hashlib.sha256()
        h.update(data)
        return h.hexdigest()
