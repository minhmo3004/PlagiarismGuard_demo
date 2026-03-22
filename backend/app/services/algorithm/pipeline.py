"""
Pipeline thuật toán chính
Điều phối toàn bộ quy trình: tiền xử lý → tạo shingles → MinHash → LSH
"""
from typing import Dict
from ..preprocessing.pipeline import PreprocessingPipeline
from .shingling import create_shingles
from .minhash import create_minhash_signature
from .lsh_index import LSHIndex


class PlagiarismPipeline:
    """
    Pipeline chính từ file tài liệu đến chỉ mục LSH
    
    Quy trình hoạt động:
    1. Tiền xử lý file (trích xuất văn bản, tokenize)
    2. Tạo shingles (k=7)
    3. Tạo chữ ký MinHash (128 permutations, seed=42)
    4. Chèn hoặc truy vấn chỉ mục LSH (ngưỡng tương đồng mặc định 0.4)
    """
    
    def __init__(self, threshold: float = 0.4):
        """
        Khởi tạo pipeline
        
        Args:
            threshold: Ngưỡng tương đồng Jaccard cho LSH (mặc định 0.4)
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
        Lập chỉ mục (index) một tài liệu vào LSH corpus
        
        Args:
            file_path: Đường dẫn đến file tài liệu
            file_type: Đuôi file (pdf, docx, txt, tex)
            doc_id: Mã định danh duy nhất của tài liệu
        
        Returns:
            Dictionary chứa metadata về quá trình lập chỉ mục
        
        Ví dụ:
            metadata = pipeline.index_document(
                "thesis.pdf", 
                "pdf", 
                "doc_123"
            )
            # Kết quả ví dụ:
            # {
            #     "file_type": "pdf",
            #     "method": "native",
            #     "page_count": 50,
            #     "token_count": 15000,
            #     "shingle_count": 14994
            # }
        """
        # 1. Tiền xử lý tài liệu
        tokens, metadata = self.preprocessor.process(file_path, file_type)
        
        # 2. Tạo shingles từ tokens
        shingles = create_shingles(tokens, k=7)
        metadata["shingle_count"] = len(shingles)
        
        # 3. Tạo chữ ký MinHash
        signature = create_minhash_signature(shingles)
        
        # 4. Chèn vào chỉ mục LSH
        self.lsh_index.insert(doc_id, signature)
        
        return metadata
    
    def check_document(
        self, 
        file_path: str, 
        file_type: str, 
        top_k: int = 10
    ) -> Dict:
        """
        Kiểm tra đạo văn cho một tài liệu query so với toàn bộ corpus
        
        Args:
            file_path: Đường dẫn đến file tài liệu cần kiểm tra
            file_type: Đuôi file
            top_k: Số lượng tài liệu tương đồng tối đa trả về (mặc định 10)
        
        Returns:
            Dictionary chứa metadata và danh sách candidate
        
        Ví dụ:
            result = pipeline.check_document("query.pdf", "pdf", top_k=5)
            # Kết quả ví dụ:
            # {
            #     "metadata": {...},
            #     "candidates": [
            #         ("doc_123", 0.85),
            #         ("doc_456", 0.72)
            #     ],
            #     "candidate_count": 2
            # }
        """
        # 1. Tiền xử lý tài liệu query
        tokens, metadata = self.preprocessor.process(file_path, file_type)
        
        # 2-3. Tạo shingles và MinHash signature
        shingles = create_shingles(tokens, k=7)
        signature = create_minhash_signature(shingles)
        
        # 4. Truy vấn LSH để tìm candidate
        candidates = self.lsh_index.query(signature, top_k=top_k)
        
        return {
            "metadata": metadata,
            "candidates": candidates,
            "candidate_count": len(candidates)
        }
    
    def get_index_stats(self) -> Dict:
        """
        Lấy thông tin thống kê của chỉ mục LSH
        
        Returns:
            Dictionary chứa số lượng tài liệu, ngưỡng, số permutation, v.v.
        """
        return self.lsh_index.get_stats()