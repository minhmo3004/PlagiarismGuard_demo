"""
Module MinHash
Tạo chữ ký MinHash từ tập hợp shingles để ước lượng độ tương đồng Jaccard nhanh chóng
"""
from datasketch import MinHash
from typing import Set

# QUAN TRỌNG: Các giá trị này PHẢI cố định để đảm bảo tính tái lập (reproducibility)
MINHASH_SEED = 42           # Seed cố định, không được random
MINHASH_PERMUTATIONS = 128  # Số lượng permutation - sai số ước lượng ≈ 1/√128 ≈ 8.8%


def create_minhash_signature(shingles: Set[int]) -> MinHash:
    """
    Tạo chữ ký MinHash từ tập hợp shingles
    
    MinHash nén một tập hợp hàng nghìn shingles thành một chữ ký có kích thước cố định.
    Tính chất toán học: Xác suất MinHash(A) = MinHash(B) ≈ Jaccard(A, B)
    
    Args:
        shingles: Tập hợp các giá trị hash của shingles (số nguyên 32-bit)
    
    Returns:
        Đối tượng MinHash chứa chữ ký đã tạo
    
    Raises:
        ValueError: Nếu tập shingles rỗng
    
    Ví dụ:
        shingles = {123456, 789012, 345678}
        signature = create_minhash_signature(shingles)
        # signature là một MinHash object với 128 permutations
    """
    if not shingles:
        raise ValueError("Tập hợp shingles không được rỗng")
    
    # Tạo MinHash với seed cố định để đảm bảo kết quả lặp lại được
    m = MinHash(num_perm=MINHASH_PERMUTATIONS, seed=MINHASH_SEED)
    
    for shingle in shingles:
        # Chuyển thành bytes để update vào MinHash
        # MinHash.update() yêu cầu dữ liệu dạng bytes
        m.update(str(shingle).encode('utf-8'))
    
    return m


def estimate_jaccard(sig1: MinHash, sig2: MinHash) -> float:
    """
    Ước lượng độ tương đồng Jaccard giữa hai chữ ký MinHash
    
    Args:
        sig1: Chữ ký MinHash thứ nhất
        sig2: Chữ ký MinHash thứ hai
    
    Returns:
        Giá trị Jaccard ước lượng (trong khoảng 0.0 đến 1.0)
    
    Ví dụ:
        jaccard = estimate_jaccard(sig1, sig2)
        # jaccard ≈ 0.75 nghĩa là độ tương đồng ước tính khoảng 75%
    """
    return sig1.jaccard(sig2)