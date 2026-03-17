"""
Shingling module
Creates k-shingles (n-grams) from tokenized text
"""
from typing import Set, List, Tuple, Dict
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


def create_shingles_with_positions(tokens: List[str], k: int = 7) -> Tuple[Set[int], Dict[int, List[Tuple[int, int, str]]]]:
    """
    Tạo shingles với thông tin vị trí để hỗ trợ highlight matched segments.
    
    Args:
        tokens: List các từ đã tokenize
        k: Kích thước shingle (số từ)
    
    Returns:
        Tuple gồm:
        - Set các hash values
        - Dict mapping hash -> list of (start_token_idx, end_token_idx, original_text)
    
    Example:
        tokens = ["Trí_tuệ", "nhân_tạo", "đang", "phát_triển", "mạnh"]
        shingles, positions = create_shingles_with_positions(tokens, k=3)
        # positions = {
        #     hash1: [(0, 3, "Trí_tuệ nhân_tạo đang")],
        #     hash2: [(1, 4, "nhân_tạo đang phát_triển")],
        #     hash3: [(2, 5, "đang phát_triển mạnh")]
        # }
    """
    if len(tokens) < k:
        shingle = " ".join(tokens)
        hash_val = mmh3.hash(shingle, signed=False)
        return {hash_val}, {hash_val: [(0, len(tokens), shingle)]}
    
    shingle_set = set()
    positions: Dict[int, List[Tuple[int, int, str]]] = {}
    
    for i in range(len(tokens) - k + 1):
        shingle = " ".join(tokens[i:i+k])
        hash_value = mmh3.hash(shingle, signed=False)
        
        shingle_set.add(hash_value)
        
        # Store position info
        if hash_value not in positions:
            positions[hash_value] = []
        positions[hash_value].append((i, i + k, shingle))
    
    return shingle_set, positions


def find_common_shingles(
    query_tokens: List[str], 
    source_tokens: List[str], 
    k: int = 7
) -> List[Dict]:
    """
    Tìm các shingles chung giữa query và source document.
    Merge các shingle liên tiếp/chồng lấn thành đoạn text đầy đủ.
    
    Args:
        query_tokens: Tokens của query document
        source_tokens: Tokens của source document
        k: Kích thước shingle
    
    Returns:
        List các matched segments với thông tin vị trí và FULL text
    """
    query_shingles, query_positions = create_shingles_with_positions(query_tokens, k)
    source_shingles, source_positions = create_shingles_with_positions(source_tokens, k)
    
    common_hashes = query_shingles & source_shingles
    
    if not common_hashes:
        return []
    
    # Collect all matched token ranges (not text - rebuild later)
    matched_ranges = []
    for hash_val in common_hashes:
        if hash_val in query_positions and hash_val in source_positions:
            for q_start, q_end, _ in query_positions[hash_val]:
                for s_start, s_end, _ in source_positions[hash_val]:
                    matched_ranges.append({
                        "query_start": q_start,
                        "query_end": q_end,
                        "source_start": s_start,
                        "source_end": s_end,
                    })
    
    if not matched_ranges:
        return []
    
    # Sort by query position
    matched_ranges.sort(key=lambda x: x["query_start"])
    
    # Merge overlapping/adjacent ranges
    merged_ranges = [matched_ranges[0].copy()]
    for rng in matched_ranges[1:]:
        last = merged_ranges[-1]
        # Merge if overlapping or adjacent (within 2 tokens gap)
        if rng["query_start"] <= last["query_end"] + 2:
            last["query_end"] = max(last["query_end"], rng["query_end"])
            last["source_end"] = max(last["source_end"], rng["source_end"])
        else:
            merged_ranges.append(rng.copy())
    
    # Rebuild full text from token ranges
    segments = []
    for rng in merged_ranges:
        q_start = rng["query_start"]
        q_end = min(rng["query_end"], len(query_tokens))
        s_start = rng["source_start"]
        s_end = min(rng["source_end"], len(source_tokens))
        
        query_text = " ".join(query_tokens[q_start:q_end])
        source_text = " ".join(source_tokens[s_start:s_end])
        
        # Only include segments with meaningful length (>= 2 words visible)
        if len(query_text.split()) >= 2:
            segments.append({
                "query_start": q_start,
                "query_end": q_end,
                "query_text": query_text,
                "source_start": s_start,
                "source_end": s_end,
                "source_text": source_text,
            })
    
    # Sort by length (longest first) so most important segments show first
    segments.sort(key=lambda x: x["query_end"] - x["query_start"], reverse=True)
    
    return segments

