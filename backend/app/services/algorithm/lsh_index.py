"""
LSH Index module
Locality Sensitive Hashing for fast similarity search
"""
from datasketch import MinHash, MinHashLSH
from typing import List, Tuple, Dict


class LSHIndex:
    """
    Wrapper around datasketch MinHashLSH
    
    LSH uses banding technique to find candidate pairs:
    - Divides signature into b bands of r rows each
    - Two documents are candidates if they match in at least one band
    - Probability: P(candidate) = 1 - (1 - s^r)^b
    
    Configuration:
        threshold=0.4, b=32, r=4 (b*r = 128)
        - s=0.5: P ≈ 86% detection
        - s=0.2: P ≈ 5% false positive
    """
    
    def __init__(self, threshold: float = 0.4, num_perm: int = 128):
        """
        Initialize LSH index
        
        Args:
            threshold: Jaccard similarity threshold (default 0.4)
            num_perm: Number of permutations (must match MinHash, default 128)
        """
        self.threshold = threshold
        self.num_perm = num_perm
        self.lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
        self.signatures: Dict[str, MinHash] = {}  # doc_id -> MinHash
    
    def insert(self, doc_id: str, minhash: MinHash) -> None:
        """
        Insert document vào index
        
        Args:
            doc_id: Unique document identifier
            minhash: MinHash signature of the document
        """
        self.lsh.insert(doc_id, minhash)
        self.signatures[doc_id] = minhash
    
    def query(self, minhash: MinHash, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Query để tìm candidate documents
        
        Args:
            minhash: MinHash signature of query document
            top_k: Maximum number of results to return
        
        Returns:
            List of (doc_id, estimated_jaccard) sorted by similarity descending
        
        Example:
            results = lsh_index.query(query_minhash, top_k=5)
            # [('doc123', 0.85), ('doc456', 0.72), ...]
        """
        # Get candidates from LSH
        candidates = self.lsh.query(minhash)
        
        # Calculate exact Jaccard for candidates
        results = []
        for doc_id in candidates:
            if doc_id in self.signatures:
                jaccard = minhash.jaccard(self.signatures[doc_id])
                results.append((doc_id, jaccard))
        
        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]
    
    def remove(self, doc_id: str) -> None:
        """
        Remove document from index
        
        Args:
            doc_id: Document identifier to remove
        """
        if doc_id in self.signatures:
            self.lsh.remove(doc_id)
            del self.signatures[doc_id]
    
    def get_stats(self) -> Dict:
        """
        Get index statistics
        
        Returns:
            Dict with index stats
        """
        return {
            "total_documents": len(self.signatures),
            "threshold": self.threshold,
            "num_perm": self.num_perm
        }
