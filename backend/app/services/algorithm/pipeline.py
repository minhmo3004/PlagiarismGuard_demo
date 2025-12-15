"""
Algorithm Pipeline
Orchestrates preprocessing, shingling, MinHash, and LSH
"""
from typing import Dict
from ..preprocessing.pipeline import PreprocessingPipeline
from .shingling import create_shingles
from .minhash import create_minhash_signature
from .lsh_index import LSHIndex


class PlagiarismPipeline:
    """
    Main pipeline từ file đến LSH index
    
    Workflow:
    1. Preprocess file (extract text, tokenize)
    2. Create shingles (k=7)
    3. Create MinHash signature (P=128, seed=42)
    4. Insert/Query LSH index (threshold=0.4)
    """
    
    def __init__(self, threshold: float = 0.4):
        """
        Initialize pipeline
        
        Args:
            threshold: LSH similarity threshold (default 0.4)
        """
        self.preprocessor = PreprocessingPipeline()
        self.lsh_index = LSHIndex(threshold=threshold)
        self.threshold = threshold
    
    def index_document(
        self, 
        file_path: str, 
        file_type: str, 
        doc_id: str
    ) -> Dict:
        """
        Index một document vào LSH
        
        Args:
            file_path: Path to document file
            file_type: File extension (pdf, docx, txt, tex)
            doc_id: Unique document identifier
        
        Returns:
            Metadata về quá trình indexing
        
        Example:
            metadata = pipeline.index_document(
                "thesis.pdf", 
                "pdf", 
                "doc_123"
            )
            # metadata = {
            #     "file_type": "pdf",
            #     "method": "native",
            #     "page_count": 50,
            #     "token_count": 15000,
            #     "shingle_count": 14994
            # }
        """
        # 1. Preprocess
        tokens, metadata = self.preprocessor.process(file_path, file_type)
        
        # 2. Create shingles
        shingles = create_shingles(tokens, k=7)
        metadata["shingle_count"] = len(shingles)
        
        # 3. Create MinHash signature
        signature = create_minhash_signature(shingles)
        
        # 4. Insert vào LSH
        self.lsh_index.insert(doc_id, signature)
        
        return metadata
    
    def check_document(
        self, 
        file_path: str, 
        file_type: str, 
        top_k: int = 10
    ) -> Dict:
        """
        Check một document với corpus
        
        Args:
            file_path: Path to query document
            file_type: File extension
            top_k: Maximum number of similar documents to return
        
        Returns:
            Dict chứa matches và metadata
        
        Example:
            result = pipeline.check_document("query.pdf", "pdf", top_k=5)
            # result = {
            #     "metadata": {...},
            #     "candidates": [
            #         ("doc_123", 0.85),
            #         ("doc_456", 0.72)
            #     ],
            #     "candidate_count": 2
            # }
        """
        # 1. Preprocess
        tokens, metadata = self.preprocessor.process(file_path, file_type)
        
        # 2-3. Shingle + MinHash
        shingles = create_shingles(tokens, k=7)
        signature = create_minhash_signature(shingles)
        
        # 4. Query LSH
        candidates = self.lsh_index.query(signature, top_k=top_k)
        
        return {
            "metadata": metadata,
            "candidates": candidates,
            "candidate_count": len(candidates)
        }
    
    def get_index_stats(self) -> Dict:
        """Get LSH index statistics"""
        return self.lsh_index.get_stats()
