"""
Dịch vụ Kiểm tra Đạo văn
Kết nối tất cả các modules để kiểm tra đạo văn

Tính năng: check_against_corpus: Kiểm tra 1 file với corpus
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
class MatchedSegment:
    """Một đoạn văn bản trùng khớp cụ thể"""
    query_text: str
    query_start: int
    query_end: int
    source_text: str
    source_start: int
    source_end: int


@dataclass
class CorpusMatch:
    """Một tài liệu khớp từ corpus với chi tiết các đoạn trùng khớp"""
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
    """Service chính cho việc phát hiện đạo văn"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        # Khởi tạo LSH index
        self.lsh_index = LSHIndex(
            threshold=settings.LSH_THRESHOLD,
            num_perm=settings.MINHASH_PERMUTATIONS
        )
        
        # Load corpus từ Redis
        if redis_client:
            self._load_corpus()
    
    def _load_corpus(self):
        """Load corpus từ Redis vào LSH index"""
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
                    
                    # Tái tạo MinHash từ JSON với cùng seed
                    from app.services.algorithm.minhash import MINHASH_SEED
                    minhash = MinHash(num_perm=settings.MINHASH_PERMUTATIONS, seed=MINHASH_SEED)
                    hashvalues = json.loads(sig_data)
                    minhash.hashvalues = np.array(hashvalues, dtype=np.uint64)
                    
                    self.lsh_index.insert(doc_id, minhash)
                    loaded += 1
            
            print(f"✅ Đã load {loaded} tài liệu vào LSH index")
        except Exception as e:
            print(f"⚠️ Không thể load corpus: {e}")
    
    def _get_text_from_postgres(self, doc_id: str, pg_id: str = None) -> str:
        """
        Lấy văn bản tài liệu từ PostgreSQL thay vì Redis.
        Giúp tiết kiệm RAM vì Redis chạy trong memory.
        
        Args:
            doc_id: ID ngắn của tài liệu (8 ký tự từ UUID)
            pg_id: UUID đầy đủ của PostgreSQL  có trong metadata Redis
        
        Returns:
            Văn bản trích xuất được hoặc None nếu không tìm thấy
        """
        try:
            db = SessionLocal()
            try:
                import uuid as uuid_module
                doc = None
                
                # Phương pháp 1: Thử với pg_id (UUID đầy đủ)
                if pg_id:
                    try:
                        full_uuid = uuid_module.UUID(pg_id)
                        doc = db.query(Document).filter(Document.id == full_uuid).first()
                    except (ValueError, AttributeError):
                        pass
                
                # Phương pháp 2: Thử UUID được padding (doc_id + số 0)
                if not doc:
                    full_uuid_str = doc_id + '0' * (32 - len(doc_id))
                    try:
                        full_uuid = uuid_module.UUID(full_uuid_str)
                        doc = db.query(Document).filter(Document.id == full_uuid).first()
                    except ValueError:
                        pass
                
                # Phương pháp 3: Tìm theo prefix ID
                if not doc:
                    from sqlalchemy import cast, String
                    doc = db.query(Document).filter(
                        Document.is_corpus == 1,
                        Document.extracted_text.isnot(None),
                        cast(Document.id, String).like(f"{doc_id}%")
                    ).first()
                
                # Phương pháp 4: Fallback - tìm theo hash prefix
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
            print(f"⚠️ Lỗi khi truy vấn PostgreSQL cho tài liệu {doc_id}: {e}")
            return None
    
    def _extract_text(self, file_path: str, filename: str) -> str:
        """Trích xuất văn bản từ file"""
        ext = os.path.splitext(filename)[1].lower()
        
        if ext == '.pdf':
            from app.services.preprocessing.pdf_extractor import extract_text_from_pdf
            return extract_text_from_pdf(file_path)
        elif ext == '.docx':
            from docx import Document
            try:
                # Thêm delay để đảm bảo file đã được ghi hoàn tất trên Windows
                import time
                time.sleep(0.5)
                
                # Kiểm tra file tồn tại và có thể đọc
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Không tìm thấy file DOCX: {file_path}")
                
                if os.path.getsize(file_path) == 0:
                    raise ValueError("File DOCX trống")
                
                doc = Document(file_path)
                text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
                
                if not text.strip():
                    raise ValueError("Không tìm thấy nội dung văn bản trong file DOCX")
                
                return text
                    
            except Exception as e:
                print(f"❌ Lỗi khi đọc file DOCX: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Không thể đọc file DOCX: {str(e)}. Vui lòng đảm bảo file là tài liệu Word hợp lệ."
                )
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    
    def _process_text(self, text: str) -> Tuple[List[str], MinHash]:
        """Xử lý văn bản → tokens → shingles → MinHash"""
        # Chuẩn hóa văn bản
        text = normalize_text(text)
        
        # Tokenize (Vietnamese NLP)
        tokens = preprocess_vietnamese(text)
        
        # Tạo shingles
        shingles = create_shingles(tokens, k=settings.SHINGLE_SIZE)
        
        # Tạo chữ ký MinHash
        minhash = create_minhash_signature(shingles)
        
        return tokens, minhash
    
    # ═══════════════════════════════════════════════════════════
    # TÍNH NĂNG: Kiểm tra 1 file với corpus
    # ═══════════════════════════════════════════════════════════
    
    def check_against_corpus(self, file_path: str, filename: str) -> PlagiarismResult:
        """
        Kiểm tra một file với corpus
        
        Args:
            file_path: Đường dẫn đến file
            filename: Tên file
        
        Returns:
            PlagiarismResult chứa các matches từ corpus (bao gồm chi tiết từng đoạn trùng khớp)
        """
        start_time = time.time()
        
        # Trích xuất và xử lý văn bản
        text = self._extract_text(file_path, filename)
        tokens, minhash = self._process_text(text)
        
        # Truy vấn LSH index
        candidates = self.lsh_index.query(minhash, top_k=20)
        
        # Xây dựng danh sách matches với matched segments
        matches = []
        for doc_id, similarity in candidates:
            if similarity >= 0.2:  # Tối thiểu 20% độ tương đồng
                # Lấy metadata từ Redis
                metadata = {}
                source_text = None
                pg_id = None
                
                if self.redis_client:
                    # Lấy metadata từ Redis (nhanh, nhẹ)
                    meta_key = f"doc:meta:{doc_id}"
                    metadata = self.redis_client.hgetall(meta_key)
                    if metadata and isinstance(list(metadata.keys())[0], bytes):
                        metadata = {k.decode(): v.decode() for k, v in metadata.items()}
                    
                    # Lấy pg_id để truy vấn PostgreSQL
                    pg_id = metadata.get('pg_id')
                
                # Lấy văn bản gốc từ PostgreSQL (không dùng Redis để tiết kiệm RAM)
                source_text = self._get_text_from_postgres(doc_id, pg_id)
                
                # Tìm các đoạn trùng khớp nếu có văn bản nguồn
                matched_segments = []
                if source_text:
                    source_tokens = preprocess_vietnamese(normalize_text(source_text))
                    segments_data = find_common_shingles(tokens, source_tokens, k=settings.SHINGLE_SIZE)
                    
                    # Hiển thị tối đa 50 đoạn mỗi match (sắp xếp theo độ dài, dài nhất trước)
                    for seg in segments_data[:50]:
                        matched_segments.append(MatchedSegment(
                            query_text=seg["query_text"],
                            query_start=seg["query_start"],
                            query_end=seg["query_end"],
                            source_text=seg["source_text"],
                            source_start=seg["source_start"],
                            source_end=seg["source_end"]
                        ))
                
                matches.append(CorpusMatch(
                    doc_id=doc_id,
                    title=metadata.get('title', 'Unknown'),
                    author=metadata.get('author', 'Unknown'),
                    university=metadata.get('university', 'Unknown'),
                    year=int(metadata.get('year', 0)) or None,
                    similarity=similarity,
                    matched_segments=matched_segments if matched_segments else None
                ))
        
        # Sắp xếp theo độ tương đồng giảm dần
        matches.sort(key=lambda x: x.similarity, reverse=True)
        matches = matches[:10]  # Top 10
        
        # Tính độ tương đồng tổng thể
        overall_sim = matches[0].similarity if matches else 0.0
        
        # Xác định mức độ đạo văn
        if overall_sim >= 0.7:
            level = "high"
            is_plagiarized = True
        elif overall_sim >= 0.4:
            level = "medium"
            is_plagiarized = True
        elif overall_sim >= 0.2:
            level = "low"
            is_plagiarized = True
        else:
            level = "none"
            is_plagiarized = False
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return PlagiarismResult(
            is_plagiarized=is_plagiarized,
            overall_similarity=overall_sim,
            plagiarism_level=level,
            matches=matches,
            word_count=len(tokens),
            processing_time_ms=processing_time
        )
    
    # ═══════════════════════════════════════════════════════════
    # QUẢN LÝ CORPUS
    # ═══════════════════════════════════════════════════════════
    
    def add_to_corpus(self, doc_id: str, text: str, metadata: Dict) -> bool:
        """Thêm một tài liệu vào corpus"""
        try:
            tokens, minhash = self._process_text(text)
            
            # Thêm vào LSH index
            self.lsh_index.insert(doc_id, minhash)
            
            # Lưu vào Redis nếu có
            if self.redis_client:
                # Lưu chữ ký
                self.redis_client.set(f"doc:sig:{doc_id}", minhash.digest().hex())
                
                # Lưu metadata
                self.redis_client.hset(f"doc:meta:{doc_id}", mapping=metadata)
            
            return True
        except Exception as e:
            print(f"Lỗi khi thêm vào corpus: {e}")
            return False
    
    def get_corpus_stats(self) -> Dict:
        """Lấy thống kê corpus"""
        return self.lsh_index.get_stats()