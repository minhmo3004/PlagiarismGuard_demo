import redis
from datasketch import MinHash
from app.config import settings
from app.services.algorithm.lsh_index import LSHIndex
import logging

logger = logging.getLogger(__name__)


class SimilarityService:
    """Dịch vụ xử lý tìm kiếm độ tương đồng sử dụng MinHash + LSH"""
    
    def __init__(self, redis_url: str = None):
        """
        Khởi tạo dịch vụ
        
        Args:
            redis_url: URL kết nối Redis (nếu không truyền sẽ dùng config mặc định)
        """
        # Kết nối Redis
        self.redis_client = redis.Redis.from_url(redis_url or settings.REDIS_URL)
        
        # Khởi tạo LSH index
        self.lsh_index = LSHIndex(
            threshold=settings.LSH_THRESHOLD,
            num_perm=settings.MINHASH_PERMUTATIONS
        )
        
        # Tải các chữ ký (signature) đã có từ Redis vào LSH
        try:
            keys = self.redis_client.keys("doc:sig:*")
            for k in keys:
                doc_id = k.decode().split(":", 2)[2]
                data = self.redis_client.get(k)
                
                if data:
                    # Khôi phục MinHash từ dữ liệu đã serialize
                    mh = MinHash.deserialize(data)
                    self.lsh_index.insert(doc_id, mh)
                    
        except Exception as e:
            logger.warning(f"Không thể tải signature từ Redis: {e}")

    def index_signature(self, doc_id: str, minhash: MinHash):
        """
        Lưu chữ ký MinHash vào Redis và thêm vào LSH index
        
        Args:
            doc_id: ID của tài liệu
            minhash: Chữ ký MinHash của tài liệu
        """
        try:
            # Lưu vào Redis
            self.redis_client.set(f"doc:sig:{doc_id}", minhash.serialize())
            
            # Thêm vào LSH index
            self.lsh_index.insert(doc_id, minhash)
            
        except Exception as e:
            logger.error(f"Lỗi khi lập chỉ mục signature: {e}")

    def query(self, minhash: MinHash, top_k: int = 10):
        """
        Truy vấn các tài liệu tương tự từ LSH index
        
        Args:
            minhash: Chữ ký MinHash của tài liệu cần so sánh
            top_k: Số lượng kết quả trả về
        
        Returns:
            Danh sách các tài liệu tương tự (doc_id, similarity_score)
        """
        return self.lsh_index.query(minhash, top_k=top_k)