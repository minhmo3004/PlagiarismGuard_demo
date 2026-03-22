"""
Module chỉ mục LSH (Locality Sensitive Hashing)
Sử dụng để tìm kiếm nhanh tài liệu tương đồng dựa trên Jaccard similarity
"""
from datasketch import MinHash, MinHashLSH
from typing import List, Tuple, Dict


class LSHIndex:
    """
    Lớp bọc quanh MinHashLSH của thư viện datasketch
    
    Nguyên lý hoạt động của LSH:
    - Chia signature thành b bands, mỗi band có r rows
    - Hai tài liệu được coi là candidate nếu chúng khớp ít nhất ở một band
    - Xác suất phát hiện: P(candidate) = 1 - (1 - s^r)^b
    
    Cấu hình mặc định:
        threshold=0.4, num_perm=128 (b=32, r=4 → b*r=128)
        - Với similarity s=0.5: Xác suất phát hiện ≈ 86%
        - Với similarity s=0.2: Xác suất false positive ≈ 5%
    """
    
    def __init__(self, threshold: float = 0.4, num_perm: int = 128):
        """
        Khởi tạo chỉ mục LSH
        
        Args:
            threshold: Ngưỡng Jaccard similarity tối thiểu (mặc định 0.4)
            num_perm: Số lượng permutation (phải khớp với MinHash, mặc định 128)
        """
        self.threshold = threshold
        self.num_perm = num_perm
        self.lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
        self.signatures: Dict[str, MinHash] = {}  # doc_id -> MinHash
    
    def insert(self, doc_id: str, minhash: MinHash) -> None:
        """
        Thêm một tài liệu vào chỉ mục LSH
        
        Args:
            doc_id: Mã định danh duy nhất của tài liệu
            minhash: Chữ ký MinHash của tài liệu
        """
        self.lsh.insert(doc_id, minhash)
        self.signatures[doc_id] = minhash
    
    def query(self, minhash: MinHash, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Tìm kiếm các tài liệu candidate tương đồng với tài liệu query
        
        Args:
            minhash: Chữ ký MinHash của tài liệu query
            top_k: Số lượng kết quả tối đa trả về (mặc định 10)
        
        Returns:
            Danh sách các cặp (doc_id, estimated_jaccard) được sắp xếp giảm dần theo độ tương đồng
        
        Ví dụ:
            results = lsh_index.query(query_minhash, top_k=5)
            # Kết quả: [('doc123', 0.85), ('doc456', 0.72), ...]
        """
        # Lấy danh sách candidate từ LSH
        candidates = self.lsh.query(minhash)
        
        # Tính Jaccard similarity chính xác cho từng candidate
        results = []
        for doc_id in candidates:
            if doc_id in self.signatures:
                jaccard = minhash.jaccard(self.signatures[doc_id])
                results.append((doc_id, jaccard))
        
        # Sắp xếp theo độ tương đồng giảm dần
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]
    
    def remove(self, doc_id: str) -> None:
        """
        Xóa một tài liệu khỏi chỉ mục LSH
        
        Args:
            doc_id: Mã định danh của tài liệu cần xóa
        """
        if doc_id in self.signatures:
            self.lsh.remove(doc_id)
            del self.signatures[doc_id]
    
    def get_stats(self) -> Dict:
        """
        Lấy thông tin thống kê của chỉ mục
        
        Returns:
            Dictionary chứa các thông tin thống kê
        """
        return {
            "total_documents": len(self.signatures),
            "threshold": self.threshold,
            "num_perm": self.num_perm
        }