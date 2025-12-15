"""
Vietnamese NLP module
Handles Vietnamese word segmentation using underthesea
"""
from underthesea import word_tokenize
from typing import List
from .text_normalizer import normalize_text


def vietnamese_tokenize(text: str) -> List[str]:
    """
    Tách từ tiếng Việt và nối lại bằng underscore
    
    Vietnamese is a monosyllabic language. Multi-word phrases like
    "trí tuệ nhân tạo" (artificial intelligence) should be kept together.
    
    Args:
        text: Vietnamese text
    
    Returns:
        List of tokens with compound words joined by underscore
    
    Example:
        Input:  "Trí tuệ nhân tạo đang phát triển mạnh"
        Output: ["Trí_tuệ", "nhân_tạo", "đang", "phát_triển", "mạnh"]
    """
    # underthesea returns tokens with spaces for compound words
    tokens = word_tokenize(text)
    
    # Nối các từ ghép bằng underscore
    # This preserves compound words as single tokens
    return [token.replace(" ", "_") for token in tokens]


def preprocess_vietnamese(text: str) -> List[str]:
    """
    Full preprocessing pipeline cho tiếng Việt
    
    Steps:
    1. Normalize text (Unicode, lowercase, whitespace)
    2. Word segmentation (Vietnamese-specific)
    
    Args:
        text: Raw Vietnamese text
    
    Returns:
        List of preprocessed tokens
    """
    # 1. Normalize
    text = normalize_text(text)
    
    # 2. Word segmentation
    tokens = vietnamese_tokenize(text)
    
    return tokens
