"""
MinHash module
Creates MinHash signatures from shingle sets
"""
from datasketch import MinHash
from typing import Set

# CRITICAL: These values MUST be fixed for reproducibility
MINHASH_SEED = 42  # PHẢI cố định, không random
MINHASH_PERMUTATIONS = 128  # Error ≈ 1/√128 ≈ 8.8%


def create_minhash_signature(shingles: Set[int]) -> MinHash:
    """
    Tạo MinHash signature từ set shingles
    
    MinHash compresses a set of thousands of shingles into a fixed-size signature.
    Mathematical property: P(MinHash(A) = MinHash(B)) = Jaccard(A, B)
    
    Args:
        shingles: Set các shingle hash values (32-bit integers)
    
    Returns:
        MinHash object với signature
    
    Raises:
        ValueError: If shingle set is empty
    
    Example:
        shingles = {123456, 789012, 345678}
        signature = create_minhash_signature(shingles)
        # signature is a MinHash object with 128 permutations
    """
    if not shingles:
        raise ValueError("Shingle set cannot be empty")
    
    # Create MinHash with fixed seed for reproducibility
    m = MinHash(num_perm=MINHASH_PERMUTATIONS, seed=MINHASH_SEED)
    
    for shingle in shingles:
        # Encode to bytes for hashing
        # MinHash.update() expects bytes
        m.update(str(shingle).encode('utf-8'))
    
    return m


def estimate_jaccard(sig1: MinHash, sig2: MinHash) -> float:
    """
    Ước lượng Jaccard similarity từ 2 signatures
    
    Args:
        sig1: First MinHash signature
        sig2: Second MinHash signature
    
    Returns:
        Estimated Jaccard similarity (0.0 to 1.0)
    
    Example:
        jaccard = estimate_jaccard(sig1, sig2)
        # jaccard ≈ 0.75 means 75% similar
    """
    return sig1.jaccard(sig2)
