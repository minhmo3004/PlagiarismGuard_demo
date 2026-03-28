"""
Plagiarism Checker Service
Kết nối tất cả modules để check đạo văn

2 Features:
1. compare_two_files: So sánh 2 files với nhau
2. check_against_corpus: Check 1 file với corpus
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
    """Kết quả so sánh 2 files"""
    similarity: float
    is_similar: bool
    file1_word_count: int
    file2_word_count: int
    processing_time_ms: int


@dataclass
class MatchedSegment:
    """Một đoạn text trùng khớp cụ thể"""
    query_text: str
    query_start: int
    query_end: int
    source_text: str
    source_start: int
    source_end: int


@dataclass
class CorpusMatch:
    """Một document match từ corpus với chi tiết các đoạn trùng khớp"""
    doc_id: str
    title: str
    author: str
    university: str
    similarity: float
    year: Optional[int] = None
    matched_segments: Optional[List[MatchedSegment]] = None


@dataclass  
class PlagiarismResult:
    """Kết quả check đạo văn với corpus"""
    is_plagiarized: bool
    overall_similarity: float
    plagiarism_level: str  # "none", "low", "medium", "high"
    matches: List[CorpusMatch]
    word_count: int
    processing_time_ms: int


class PlagiarismChecker:
    """Main service cho plagiarism detection"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        # Initialize LSH index
        self.lsh_index = LSHIndex(
            threshold=settings.LSH_THRESHOLD,
            num_perm=settings.MINHASH_PERMUTATIONS
        )
        
        # Load corpus from Redis
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
                    
                    # Reconstruct MinHash from JSON with same seed
                    from app.services.algorithm.minhash import MINHASH_SEED
                    minhash = MinHash(num_perm=settings.MINHASH_PERMUTATIONS, seed=MINHASH_SEED)
                    hashvalues = json.loads(sig_data)
                    minhash.hashvalues = np.array(hashvalues, dtype=np.uint64)
                    
                    self.lsh_index.insert(doc_id, minhash)
                    loaded += 1
            
            print(f"✅ Loaded {loaded} documents into LSH index")
        except Exception as e:
            print(f"⚠️ Could not load corpus: {e}")
    
    def _get_text_from_postgres(self, doc_id: str, pg_id: str = None) -> str:
        """
        Query document text from PostgreSQL instead of Redis.
        This saves RAM as Redis runs in memory.
        
        Args:
            doc_id: Short document ID (8 chars from UUID)
            pg_id: Full PostgreSQL UUID if available from Redis metadata
        
        Returns:
            Extracted text from document or None if not found
        """
        try:
            db = SessionLocal()
            try:
                import uuid as uuid_module
                doc = None
                
                # Method 1: Try pg_id (full UUID from Redis metadata)
                if pg_id:
                    try:
                        full_uuid = uuid_module.UUID(pg_id)
                        doc = db.query(Document).filter(Document.id == full_uuid).first()
                    except (ValueError, AttributeError):
                        pass
                
                # Method 2: Try padded UUID (doc_id + zeros)
                if not doc:
                    full_uuid_str = doc_id + '0' * (32 - len(doc_id))
                    try:
                        full_uuid = uuid_module.UUID(full_uuid_str)
                        doc = db.query(Document).filter(Document.id == full_uuid).first()
                    except ValueError:
                        pass
                
                # Method 3: Search by ID prefix using string cast
                if not doc:
                    from sqlalchemy import cast, String
                    doc = db.query(Document).filter(
                        Document.is_corpus == 1,
                        Document.extracted_text.isnot(None),
                        cast(Document.id, String).like(f"{doc_id}%")
                    ).first()
                
                # Method 4: Fallback - search any corpus doc with matching hash prefix
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
            print(f"⚠️ Error querying PostgreSQL for doc {doc_id}: {e}")
            return None
    
    def _extract_text(self, file_path: str, filename: str) -> str:
        """Extract text từ file"""
        ext = os.path.splitext(filename)[1].lower()
        
        if ext == '.pdf':
            from app.services.preprocessing.pdf_extractor import extract_text_from_pdf
            return extract_text_from_pdf(file_path)
        elif ext == '.docx':
            from docx import Document
            try:
                # Add delay to ensure file is fully written on Windows
                import time
                time.sleep(0.5)
                
                # Verify file exists and is readable
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"DOCX file not found: {file_path}")
                
                if os.path.getsize(file_path) == 0:
                    raise ValueError("DOCX file is empty")
                
                doc = Document(file_path)
                text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
                
                if not text.strip():
                    raise ValueError("No text content found in DOCX file")
                
                return text
                    
            except Exception as e:
                print(f"❌ Error reading DOCX file: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot read DOCX file: {str(e)}. Please ensure the file is a valid Word document."
                )
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    
    def _process_text(self, text: str) -> Tuple[List[str], MinHash]:
        """Process text → tokens → shingles → MinHash"""
        # Normalize
        text = normalize_text(text)
        
        # Tokenize (Vietnamese NLP)
        tokens = preprocess_vietnamese(text)
        
        # Create shingles
        shingles = create_shingles(tokens, k=settings.SHINGLE_SIZE)
        
        # Create MinHash signature
        minhash = create_minhash_signature(shingles)
        
        return tokens, minhash
    
    # ═══════════════════════════════════════════════════════════
    # FEATURE 1: So sánh 2 files với nhau
    # ═══════════════════════════════════════════════════════════
    
    def compare_two_files(self, file1_path: str, file1_name: str,
                          file2_path: str, file2_name: str) -> ComparisonResult:
        """
        So sánh 2 files với nhau
        
        Args:
            file1_path: Path to first file
            file1_name: Name of first file
            file2_path: Path to second file
            file2_name: Name of second file
        
        Returns:
            ComparisonResult với similarity score
        """
        start_time = time.time()
        
        # Extract text from both files
        text1 = self._extract_text(file1_path, file1_name)
        text2 = self._extract_text(file2_path, file2_name)
        
        # Process both texts
        tokens1, minhash1 = self._process_text(text1)
        tokens2, minhash2 = self._process_text(text2)
        
        # Calculate Jaccard similarity
        similarity = estimate_jaccard(minhash1, minhash2)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return ComparisonResult(
            similarity=similarity,
            is_similar=similarity >= 0.4,  # 40% threshold
            file1_word_count=len(tokens1),
            file2_word_count=len(tokens2),
            processing_time_ms=processing_time
        )
    
    def compare_two_texts(self, text1: str, text2: str) -> ComparisonResult:
        """So sánh 2 đoạn text trực tiếp"""
        start_time = time.time()
        
        tokens1, minhash1 = self._process_text(text1)
        tokens2, minhash2 = self._process_text(text2)
        
        similarity = estimate_jaccard(minhash1, minhash2)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return ComparisonResult(
            similarity=similarity,
            is_similar=similarity >= 0.4,
            file1_word_count=len(tokens1),
            file2_word_count=len(tokens2),
            processing_time_ms=processing_time
        )
    
    # ═══════════════════════════════════════════════════════════
    # FEATURE 2: Check 1 file với corpus
    # ═══════════════════════════════════════════════════════════
    
    def check_against_corpus(self, file_path: str, filename: str) -> PlagiarismResult:
        """
        Check 1 file với corpus
        
        Args:
            file_path: Path to file
            filename: Name of file
        
        Returns:
            PlagiarismResult với matches từ corpus (bao gồm chi tiết từng đoạn trùng khớp)
        """
        start_time = time.time()
        
        # Extract and process
        text = self._extract_text(file_path, filename)
        tokens, minhash = self._process_text(text)
        
        # Query LSH index
        candidates = self.lsh_index.query(minhash, top_k=20)
        
        # Build matches list với matched segments
        matches = []
        for doc_id, similarity in candidates:
            if similarity >= 0.2:  # Minimum 20% similarity
                # Get metadata from Redis
                metadata = {}
                source_text = None
                pg_id = None
                
                if self.redis_client:
                    # Get metadata from Redis (fast, lightweight)
                    meta_key = f"doc:meta:{doc_id}"
                    metadata = self.redis_client.hgetall(meta_key)
                    if metadata and isinstance(list(metadata.keys())[0], bytes):
                        metadata = {k.decode(): v.decode() for k, v in metadata.items()}
                    
                    # Get pg_id for PostgreSQL lookup
                    pg_id = metadata.get('pg_id')
                
                # Get source text from PostgreSQL (not Redis - saves RAM)
                # Query by pg_id or doc_id pattern matching in documents table
                source_text = self._get_text_from_postgres(doc_id, pg_id)
                
                # Find matched segments if source text available
                matched_segments = []
                if source_text:
                    source_tokens = preprocess_vietnamese(normalize_text(source_text))
                    segments_data = find_common_shingles(tokens, source_tokens, k=settings.SHINGLE_SIZE)
                    
                    # Show up to 50 segments per match (sorted by length, longest first)
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
        
        # Sort by similarity
        matches.sort(key=lambda x: x.similarity, reverse=True)
        matches = matches[:10]  # Top 10
        
        # Calculate overall similarity
        overall_sim = matches[0].similarity if matches else 0.0
        
        # Determine level
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
    # CORPUS MANAGEMENT
    # ═══════════════════════════════════════════════════════════
    
    def add_to_corpus(self, doc_id: str, text: str, metadata: Dict) -> bool:
        """Thêm 1 document vào corpus"""
        try:
            tokens, minhash = self._process_text(text)
            
            # Insert into LSH index
            self.lsh_index.insert(doc_id, minhash)
            
            # Store in Redis if available
            if self.redis_client:
                # Store signature
                self.redis_client.set(f"doc:sig:{doc_id}", minhash.digest().hex())
                
                # Store metadata
                self.redis_client.hset(f"doc:meta:{doc_id}", mapping=metadata)
            
            return True
        except Exception as e:
            print(f"Error adding to corpus: {e}")
            return False
    
    def get_corpus_stats(self) -> Dict:
        """Get corpus statistics"""
        return self.lsh_index.get_stats()
