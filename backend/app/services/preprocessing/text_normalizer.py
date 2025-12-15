"""
Text normalization module
Handles Unicode normalization, ligature expansion, case folding
"""
import unicodedata
import re

# Ligature mapping for font consistency
LIGATURE_MAP = {
    'ﬁ': 'fi', 'ﬂ': 'fl', 'ﬀ': 'ff', 
    'ﬃ': 'ffi', 'ﬄ': 'ffl', 'œ': 'oe', 'æ': 'ae'
}


def normalize_text(text: str) -> str:
    """
    Chuẩn hóa văn bản cho shingling
    
    Steps:
    1. Unicode normalization (NFKD)
    2. Ligature expansion
    3. Lowercase
    4. Whitespace collapse
    5. Strip leading/trailing
    
    Args:
        text: Raw text
    
    Returns:
        Normalized text
    """
    # 1. Unicode normalization (NFKD)
    # Decomposes characters: é → e + ´
    text = unicodedata.normalize('NFKD', text)
    
    # 2. Ligature expansion
    # Replace ligatures with separate characters
    for lig, replacement in LIGATURE_MAP.items():
        text = text.replace(lig, replacement)
    
    # 3. Lowercase
    text = text.lower()
    
    # 4. Whitespace collapse
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # 5. Strip leading/trailing
    text = text.strip()
    
    return text


def remove_vietnamese_tones(text: str) -> str:
    """
    Loại bỏ dấu tiếng Việt - chỉ dùng khi cần cross-language
    
    Note: This is NOT used for Vietnamese-only corpus.
    Only use when comparing Vietnamese with English.
    
    Args:
        text: Vietnamese text with tones
    
    Returns:
        Text without Vietnamese tones
    """
    # NFKD tách dấu ra khỏi ký tự
    text = unicodedata.normalize('NFKD', text)
    
    # Loại bỏ combining marks
    text = ''.join(c for c in text if not unicodedata.combining(c))
    
    # Xử lý đặc biệt cho đ/Đ
    text = text.replace('đ', 'd').replace('Đ', 'D')
    
    return text
