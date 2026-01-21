import redis
from datasketch import MinHash
from app.config import settings
from app.services.algorithm.lsh_index import LSHIndex
import logging

logger = logging.getLogger(__name__)


class SimilarityService:
    def __init__(self, redis_url: str = None):
        self.redis_client = redis.Redis.from_url(redis_url or settings.REDIS_URL)
        self.lsh_index = LSHIndex(threshold=settings.LSH_THRESHOLD, num_perm=settings.MINHASH_PERMUTATIONS)
        # Load existing signatures from Redis into LSH index
        try:
            keys = self.redis_client.keys("doc:sig:*")
            for k in keys:
                doc_id = k.decode().split(":", 2)[2]
                data = self.redis_client.get(k)
                if data:
                    mh = MinHash.deserialize(data)
                    self.lsh_index.insert(doc_id, mh)
        except Exception as e:
            logger.warning(f"Failed to load signatures from Redis: {e}")

    def index_signature(self, doc_id: str, minhash: MinHash):
        # store serialized signature in Redis and insert into LSH
        try:
            self.redis_client.set(f"doc:sig:{doc_id}", minhash.serialize())
            self.lsh_index.insert(doc_id, minhash)
        except Exception as e:
            logger.error(f"Error indexing signature: {e}")

    def query(self, minhash: MinHash, top_k: int = 10):
        return self.lsh_index.query(minhash, top_k=top_k)
