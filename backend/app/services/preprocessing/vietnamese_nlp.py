"""Vietnamese NLP module
Handles Vietnamese word segmentation using underthesea when available.
If underthesea is not installed or fails at runtime we fall back to a
simple whitespace tokenizer.
"""
import logging
from typing import List
from .text_normalizer import normalize_text

logger = logging.getLogger(__name__)

try:
    import underthesea as _underthesea  # type: ignore
    _UNDER_AVAILABLE = True
except Exception:
    _underthesea = None
    _UNDER_AVAILABLE = False


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
    # Validate input
    if not text or not isinstance(text, str):
        logger.debug("Invalid input: text=%r", text)
        return []
    
    # Prefer using underthesea if available
    if _UNDER_AVAILABLE and _underthesea is not None:
        try:
            # Try common call patterns for different underthesea versions.
            result = None
            if hasattr(_underthesea, "word_tokenize"):
                try:
                    result = _underthesea.word_tokenize(text, format="text")
                    logger.debug("word_tokenize(format='text') returned: %r (type: %s)", result, type(result).__name__)
                except Exception as e:
                    logger.debug("word_tokenize(format='text') raised: %s", e)
                    try:
                        result = _underthesea.word_tokenize(text)
                        logger.debug("word_tokenize() returned: %r (type: %s)", result, type(result).__name__)
                    except Exception as e2:
                        logger.debug("word_tokenize() raised: %s", e2)
            
            # older/newer versions may expose `tokenize`
            if result is None and hasattr(_underthesea, "tokenize"):
                try:
                    result = _underthesea.tokenize(text)
                    logger.debug("tokenize() returned: %r (type: %s)", result, type(result).__name__)
                except Exception as e:
                    logger.debug("tokenize() raised: %s", e)

            # If result is still None or empty, treat as failure
            if not result:
                logger.warning("underthesea returned empty/None result for text: %r", text[:50])
                raise RuntimeError("underthesea returned no result")

            # result can be a string or an iterable of tokens
            if isinstance(result, str):
                tokens = result.split()
            else:
                tokens = list(result)
            
            # Filter out empty tokens
            tokens = [t for t in tokens if t]
            tokens = [t.replace(" ", "_") for t in tokens]
            logger.debug("Tokenized %d tokens from underthesea", len(tokens))
            return tokens
        except Exception as e:
            logger.warning("underthesea failed (%s), falling back to simple tokenization", e)

    # Fallback: simple whitespace split
    if not _UNDER_AVAILABLE:
        logger.info("underthesea not available — using simple whitespace tokenizer")
    return [tok for tok in text.split() if tok]


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
