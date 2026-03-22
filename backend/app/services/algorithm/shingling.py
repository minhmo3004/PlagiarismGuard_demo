"""
Module Shingling
Tạo các k-shingle (n-gram) từ văn bản đã tokenize
"""
from typing import Set, List, Tuple, Dict
import mmh3  # Thư viện MurmurHash3


def create_shingles(tokens: List[str], k: int = 7) -> Set[int]:
    """
    Tạo tập các hash của shingle từ danh sách tokens
    
    Sử dụng kỹ thuật sliding window kết hợp MurmurHash3 để hash.
    
    Args:
        tokens: Danh sách các từ đã được tokenize
        k: Kích thước shingle (số từ). Mặc định = 7 cho tiếng Việt
    
    Returns:
        Tập các giá trị hash (số nguyên 32-bit không dấu)
    
    Ví dụ:
        tokens = ["Trí_tuệ", "nhân_tạo", "đang", "phát_triển", "mạnh"]
        shingles = create_shingles(tokens, k=3)
        # Tạo hash cho:
        # - "Trí_tuệ nhân_tạo đang"
        # - "nhân_tạo đang phát_triển"
        # - "đang phát_triển mạnh"
    """
    if len(tokens) < k:
        # Nếu văn bản quá ngắn thì dùng toàn bộ làm 1 shingle
        shingle = " ".join(tokens)
        return {mmh3.hash(shingle, signed=False)}
    
    shingle_set = set()
    for i in range(len(tokens) - k + 1):
        # Tạo shingle từ k token liên tiếp
        shingle = " ".join(tokens[i:i+k])
        
        # Hash bằng MurmurHash3 32-bit không dấu
        # signed=False đảm bảo luôn là số dương
        hash_value = mmh3.hash(shingle, signed=False)
        shingle_set.add(hash_value)
    
    return shingle_set


def create_shingles_with_positions(tokens: List[str], k: int = 7) -> Tuple[Set[int], Dict[int, List[Tuple[int, int, str]]]]:
    """
    Tạo shingle kèm thông tin vị trí để phục vụ highlight đoạn trùng
    
    Args:
        tokens: Danh sách từ đã tokenize
        k: Kích thước shingle
    
    Returns:
        Tuple gồm:
        - Tập các hash
        - Dict ánh xạ hash -> list (vị trí bắt đầu, kết thúc, text gốc)
    
    Ví dụ:
        tokens = ["Trí_tuệ", "nhân_tạo", "đang", "phát_triển", "mạnh"]
        shingles, positions = create_shingles_with_positions(tokens, k=3)
        # positions = {
        #     hash1: [(0, 3, "Trí_tuệ nhân_tạo đang")],
        #     hash2: [(1, 4, "nhân_tạo đang phát_triển")],
        #     hash3: [(2, 5, "đang phát_triển mạnh")]
        # }
    """
    if len(tokens) < k:
        # Nếu ngắn hơn k thì chỉ có 1 shingle duy nhất
        shingle = " ".join(tokens)
        hash_val = mmh3.hash(shingle, signed=False)
        return {hash_val}, {hash_val: [(0, len(tokens), shingle)]}
    
    shingle_set = set()
    positions: Dict[int, List[Tuple[int, int, str]]] = {}
    
    for i in range(len(tokens) - k + 1):
        shingle = " ".join(tokens[i:i+k])
        hash_value = mmh3.hash(shingle, signed=False)
        
        shingle_set.add(hash_value)
        
        # Lưu thông tin vị trí
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
    Tìm các shingle chung giữa document query và document nguồn
    
    Sau đó merge các shingle liên tiếp hoặc chồng lấn thành đoạn text hoàn chỉnh
    
    Args:
        query_tokens: Tokens của tài liệu cần kiểm tra
        source_tokens: Tokens của tài liệu nguồn
        k: Kích thước shingle
    
    Returns:
        Danh sách các đoạn trùng kèm thông tin vị trí và nội dung đầy đủ
    """
    query_shingles, query_positions = create_shingles_with_positions(query_tokens, k)
    source_shingles, source_positions = create_shingles_with_positions(source_tokens, k)
    
    # Lấy các hash chung
    common_hashes = query_shingles & source_shingles
    
    if not common_hashes:
        return []
    
    # Thu thập các khoảng token trùng nhau (chưa build text)
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
    
    # Sắp xếp theo vị trí trong query
    matched_ranges.sort(key=lambda x: x["query_start"])
    
    # Gộp các đoạn chồng lấn hoặc liền kề
    merged_ranges = [matched_ranges[0].copy()]
    for rng in matched_ranges[1:]:
        last = merged_ranges[-1]
        # Gộp nếu chồng lấn hoặc cách nhau tối đa 2 token
        if rng["query_start"] <= last["query_end"] + 2:
            last["query_end"] = max(last["query_end"], rng["query_end"])
            last["source_end"] = max(last["source_end"], rng["source_end"])
        else:
            merged_ranges.append(rng.copy())
    
    # Xây dựng lại text từ token
    segments = []
    for rng in merged_ranges:
        q_start = rng["query_start"]
        q_end = min(rng["query_end"], len(query_tokens))
        s_start = rng["source_start"]
        s_end = min(rng["source_end"], len(source_tokens))
        
        query_text = " ".join(query_tokens[q_start:q_end])
        source_text = " ".join(source_tokens[s_start:s_end])
        
        # Chỉ lấy đoạn có ý nghĩa (>= 2 từ)
        if len(query_text.split()) >= 2:
            segments.append({
                "query_start": q_start,
                "query_end": q_end,
                "query_text": query_text,
                "source_start": s_start,
                "source_end": s_end,
                "source_text": source_text,
            })
    
    # Sắp xếp theo độ dài giảm dần (đoạn quan trọng hiển thị trước)
    segments.sort(key=lambda x: x["query_end"] - x["query_start"], reverse=True)
    
    return segments