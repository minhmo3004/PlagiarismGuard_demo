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
    
    Args:
        query_tokens: Tokens của query document
        source_tokens: Tokens của source document
        k: Kích thước shingle
    
    Returns:
        List các matched segments với thông tin vị trí và text
    """
    query_shingles, query_positions = create_shingles_with_positions(query_tokens, k)
    source_shingles, source_positions = create_shingles_with_positions(source_tokens, k)
    
    common_hashes = query_shingles & source_shingles
    
    matched_segments = []
    for hash_val in common_hashes:
        if hash_val in query_positions and hash_val in source_positions:
            # Có thể có nhiều vị trí trong cùng 1 document
            for q_start, q_end, q_text in query_positions[hash_val]:
                for s_start, s_end, s_text in source_positions[hash_val]:
                    matched_segments.append({
                        "query_start": q_start,
                        "query_end": q_end,
                        "query_text": q_text,
                        "source_start": s_start,
                        "source_end": s_end,
                        "source_text": s_text
                    })
    
    # Sort by query position
    matched_segments.sort(key=lambda x: x["query_start"])
    
    # Merge overlapping segments
    merged = merge_overlapping_segments(matched_segments)
    
    return merged


def merge_overlapping_segments(segments: List[Dict]) -> List[Dict]:
    """
    Gộp các segments liền kề hoặc chồng lấn thành 1 segment lớn hơn.
    
    Args:
        segments: List các matched segments đã sort theo query_start
    
    Returns:
        List các merged segments
    """
    if not segments:
        return []
    
    merged = [segments[0].copy()]
    
    for seg in segments[1:]:
        last = merged[-1]
        # Nếu segment mới chồng lấn hoặc liền kề với segment trước
        if seg["query_start"] <= last["query_end"]:
            # Merge
            last["query_end"] = max(last["query_end"], seg["query_end"])
            last["query_text"] = f"{last['query_text']}..."  # Indicate merged
            last["source_end"] = max(last["source_end"], seg["source_end"])
            last["source_text"] = f"{last['source_text']}..."
        else:
            merged.append(seg.copy())
    
    return merged

