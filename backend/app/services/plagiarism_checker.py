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

from app.services.preprocessing.vietnamese_nlp import preprocess_vietnamese
from app.services.preprocessing.text_normalizer import normalize_text
from app.services.algorithm.shingling import create_shingles
from app.services.algorithm.minhash import create_minhash_signature, estimate_jaccard
from app.services.algorithm.lsh_index import LSHIndex
from app.config import settings


@dataclass
class ComparisonResult:
    """Kết quả so sánh 2 files"""
    similarity: float
    is_similar: bool
    file1_word_count: int
    file2_word_count: int
    processing_time_ms: int


@dataclass
class CorpusMatch:
    """Một document match từ corpus"""
    doc_id: str
    title: str
    author: str
    university: str
    similarity: float
    year: Optional[int] = None


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
        self.lsh_index = LSHIndex(
            threshold=settings.LSH_THRESHOLD,
            num_perm=settings.MINHASH_PERMUTATIONS
        )
        
        # Load corpus nếu có Redis
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
    
    def _extract_text(self, file_path: str, filename: str) -> str:
        """Extract text từ file"""
        ext = os.path.splitext(filename)[1].lower()
        
        if ext == '.pdf':
            from app.services.preprocessing.pdf_extractor import extract_text_from_pdf
            return extract_text_from_pdf(file_path)
        elif ext == '.docx':
            from docx import Document
            doc = Document(file_path)
            return '\n'.join([para.text for para in doc.paragraphs])
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
            PlagiarismResult với matches từ corpus
        """
        start_time = time.time()
        
        # Extract and process
        text = self._extract_text(file_path, filename)
        tokens, minhash = self._process_text(text)
        
        # Query LSH index
        candidates = self.lsh_index.query(minhash, top_k=20)
        
        # Build matches list
        matches = []
        for doc_id, similarity in candidates:
            if similarity >= 0.2:  # Minimum 20% similarity
                # Get metadata from Redis
                if self.redis_client:
                    key = f"doc:meta:{doc_id}"
                    metadata = self.redis_client.hgetall(key)
                    if isinstance(list(metadata.keys())[0] if metadata else b'', bytes):
                        metadata = {k.decode(): v.decode() for k, v in metadata.items()}
                else:
                    metadata = {}
                
                matches.append(CorpusMatch(
                    doc_id=doc_id,
                    title=metadata.get('title', 'Unknown'),
                    author=metadata.get('author', 'Unknown'),
                    university=metadata.get('university', 'Unknown'),
                    year=int(metadata.get('year', 0)) or None,
                    similarity=similarity
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
