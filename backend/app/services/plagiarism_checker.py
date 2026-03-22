"""
Dịch vụ kiểm tra đạo văn (Plagiarism Checker Service)
Kết nối tất cả các module để thực hiện kiểm tra đạo văn

Gồm 2 chức năng chính:
1. compare_two_files: So sánh hai tệp với nhau
2. check_against_corpus: So sánh một tệp với tập dữ liệu (corpus)
"""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datasketch import MinHash
import tempfile
import os
import time

from fastapi import HTTPException

from app.services.preprocessing.vietnamese_nlp import preprocess_vietnamese
from app.services.preprocessing.text_normalizer import normalize_text
from app.services.algorithm.shingling import create_shingles, find_common_shingles
from app.services.algorithm.minhash import create_minhash_signature, estimate_jaccard
from app.services.algorithm.lsh_index import LSHIndex
from app.config import settings
from app.db.database import SessionLocal
from app.db.models import Document


@dataclass
class ComparisonResult:
    """Kết quả so sánh hai tệp"""
    similarity: float
    is_similar: bool
    file1_word_count: int
    file2_word_count: int
    processing_time_ms: int


@dataclass
class MatchedSegment:
    """Một đoạn văn bản trùng khớp"""
    query_text: str
    query_start: int
    query_end: int
    source_text: str
    source_start: int
    source_end: int


@dataclass
class CorpusMatch:
    """Một tài liệu trong corpus có độ tương đồng"""
    doc_id: str
    title: str
    author: str
    university: str
    similarity: float
    year: Optional[int] = None
    matched_segments: Optional[List[MatchedSegment]] = None


@dataclass  
class PlagiarismResult:
    """Kết quả kiểm tra đạo văn với corpus"""
    is_plagiarized: bool
    overall_similarity: float
    plagiarism_level: str  # "none", "low", "medium", "high"
    matches: List[CorpusMatch]
    word_count: int
    processing_time_ms: int


class PlagiarismChecker:
    """Dịch vụ chính xử lý phát hiện đạo văn"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        
        # Khởi tạo chỉ mục LSH
        self.lsh_index = LSHIndex(
            threshold=settings.LSH_THRESHOLD,
            num_perm=settings.MINHASH_PERMUTATIONS
        )
        
        # Tải dữ liệu corpus từ Redis
        if redis_client:
            self._load_corpus()
    
    def _load_corpus(self):
        """Tải corpus từ Redis vào LSH index"""
        import json
        import numpy as np
        
        try:
            doc_keys = self.redis_client.keys("doc:sig:*")
            loaded = 0
            
            for key in doc_keys:
                doc_id = key.replace("doc:sig:", "") if isinstance(key, str) else key.decode().replace("doc:sig:", "")
                sig_data = self.redis_client.get(key)
                
                if sig_data:
                    if isinstance(sig_data, bytes):
                        sig_data = sig_data.decode()
                    
                    # Khôi phục MinHash từ JSON với cùng seed
                    from app.services.algorithm.minhash import MINHASH_SEED
                    minhash = MinHash(num_perm=settings.MINHASH_PERMUTATIONS, seed=MINHASH_SEED)
                    hashvalues = json.loads(sig_data)
                    minhash.hashvalues = np.array(hashvalues, dtype=np.uint64)
                    
                    self.lsh_index.insert(doc_id, minhash)
                    loaded += 1
            
            print(f"✅ Đã tải {loaded} tài liệu vào LSH index")
        except Exception as e:
            print(f"⚠️ Không thể tải corpus: {e}")
    
    def _get_text_from_postgres(self, doc_id: str, pg_id: str = None) -> str:
        """
        Lấy nội dung văn bản từ PostgreSQL thay vì Redis
        → Giảm sử dụng RAM do Redis lưu trên bộ nhớ
        
        Args:
            doc_id: ID rút gọn của tài liệu
            pg_id: UUID đầy đủ trong PostgreSQL (nếu có)
        
        Returns:
            Nội dung văn bản hoặc None nếu không tìm thấy
        """
        try:
            db = SessionLocal()
            try:
                import uuid as uuid_module
                doc = None
                
                # Cách 1: Tìm bằng pg_id
                if pg_id:
                    try:
                        full_uuid = uuid_module.UUID(pg_id)
                        doc = db.query(Document).filter(Document.id == full_uuid).first()
                    except (ValueError, AttributeError):
                        pass
                
                # Cách 2: Tạo UUID giả từ doc_id
                if not doc:
                    full_uuid_str = doc_id + '0' * (32 - len(doc_id))
                    try:
                        full_uuid = uuid_module.UUID(full_uuid_str)
                        doc = db.query(Document).filter(Document.id == full_uuid).first()
                    except ValueError:
                        pass
                
                # Cách 3: Tìm theo prefix ID
                if not doc:
                    from sqlalchemy import cast, String
                    doc = db.query(Document).filter(
                        Document.is_corpus == 1,
                        Document.extracted_text.isnot(None),
                        cast(Document.id, String).like(f"{doc_id}%")
                    ).first()
                
                # Cách 4: Fallback theo hash
                if not doc:
                    doc = db.query(Document).filter(
                        Document.is_corpus == 1,
                        Document.extracted_text.isnot(None)
                    ).filter(
                        Document.file_hash_sha256.like(f"{doc_id}%")
                    ).first()
                
                if doc and doc.extracted_text:
                    return doc.extracted_text
                    
                return None
            finally:
                db.close()
        except Exception as e:
            print(f"⚠️ Lỗi truy vấn PostgreSQL cho doc {doc_id}: {e}")
            return None
    
    def _extract_text(self, file_path: str, filename: str) -> str:
        """Trích xuất nội dung văn bản từ file"""
        ext = os.path.splitext(filename)[1].lower()
        
        if ext == '.pdf':
            from app.services.preprocessing.pdf_extractor import extract_text_from_pdf
            return extract_text_from_pdf(file_path)
        elif ext == '.docx':
            from docx import Document
            try:
                time.sleep(0.5)
                
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Không tìm thấy file DOCX: {file_path}")
                
                if os.path.getsize(file_path) == 0:
                    raise ValueError("File DOCX rỗng")
                
                doc = Document(file_path)
                text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
                
                if not text.strip():
                    raise ValueError("Không có nội dung trong file DOCX")
                
                return text
                    
            except Exception as e:
                print(f"❌ Lỗi đọc file DOCX: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Không thể đọc file DOCX: {str(e)}"
                )
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    
    def _process_text(self, text: str) -> Tuple[List[str], MinHash]:
        """Xử lý văn bản → token → shingles → MinHash"""
        
        # Chuẩn hóa văn bản
        text = normalize_text(text)
        
        # Tách từ tiếng Việt
        tokens = preprocess_vietnamese(text)
        
        # Tạo shingles
        shingles = create_shingles(tokens, k=settings.SHINGLE_SIZE)
        
        # Tạo chữ ký MinHash
        minhash = create_minhash_signature(shingles)
        
        return tokens, minhash