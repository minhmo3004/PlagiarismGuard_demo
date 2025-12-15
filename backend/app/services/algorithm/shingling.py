"""
Shingling module
Creates k-shingles (n-grams) from tokenized text
"""
from typing import Set, List
import mmh3  # MurmurHash3


def create_shingles(tokens: List[str], k: int = 7) -> Set[int]:
    """
    Tạo set các shingle hashes từ list tokens
    
    Uses sliding window approach with MurmurHash3 for hashing.
    
    Args:
        tokens: List các từ đã tokenize
        k: Kích thước shingle (số từ). Default=7 for Vietnamese
    
    Returns:
        Set các hash values (32-bit unsigned integers)
    
    Example:
        tokens = ["Trí_tuệ", "nhân_tạo", "đang", "phát_triển", "mạnh"]
        shingles = create_shingles(tokens, k=3)
        # Creates hashes for:
        # - "Trí_tuệ nhân_tạo đang"
        # - "nhân_tạo đang phát_triển"
        # - "đang phát_triển mạnh"
    """
    if len(tokens) < k:
        # Nếu văn bản quá ngắn, dùng toàn bộ làm 1 shingle
        shingle = " ".join(tokens)
        return {mmh3.hash(shingle, signed=False)}
    
    shingle_set = set()
    for i in range(len(tokens) - k + 1):
        # Create shingle from k consecutive tokens
        shingle = " ".join(tokens[i:i+k])
        
        # MurmurHash3 32-bit unsigned
        # signed=False ensures positive integers
        hash_value = mmh3.hash(shingle, signed=False)
        shingle_set.add(hash_value)
    
    return shingle_set
