"""
Module xử lý NLP tiếng Việt
Tách từ tiếng Việt bằng underthesea (nếu có), fallback về tách theo khoảng trắng nếu không
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
    Tách từ tiếng Việt và nối các từ ghép bằng dấu gạch dưới (_)
    
    Tiếng Việt là ngôn ngữ đơn âm tiết. Các cụm từ nhiều âm tiết như 
    "trí tuệ nhân tạo" cần được giữ nguyên thành một token.
    
    Args:
        text: Văn bản tiếng Việt
    
    Returns:
        Danh sách các token, trong đó từ ghép được nối bằng dấu _
    
    Ví dụ:
        Input:  "Trí tuệ nhân tạo đang phát triển mạnh"
        Output: ["Trí_tuệ", "nhân_tạo", "đang", "phát_triển", "mạnh"]
    """
    # Kiểm tra đầu vào
    if not text or not isinstance(text, str):
        logger.debug("Đầu vào không hợp lệ: text=%r", text)
        return []
    
    # Ưu tiên sử dụng underthesea nếu có sẵn
    if _UNDER_AVAILABLE and _underthesea is not None:
        try:
            # Thử các cách gọi phổ biến tùy phiên bản underthesea
            result = None
            if hasattr(_underthesea, "word_tokenize"):
                try:
                    result = _underthesea.word_tokenize(text, format="text")
                    logger.debug("word_tokenize(format='text') trả về: %r (kiểu: %s)", result, type(result).__name__)
                except Exception as e:
                    logger.debug("word_tokenize(format='text') lỗi: %s", e)
                    try:
                        result = _underthesea.word_tokenize(text)
                        logger.debug("word_tokenize() trả về: %r (kiểu: %s)", result, type(result).__name__)
                    except Exception as e2:
                        logger.debug("word_tokenize() lỗi: %s", e2)
            
            # Một số phiên bản cũ/mới có thể dùng tokenize
            if result is None and hasattr(_underthesea, "tokenize"):
                try:
                    result = _underthesea.tokenize(text)
                    logger.debug("tokenize() trả về: %r (kiểu: %s)", result, type(result).__name__)
                except Exception as e:
                    logger.debug("tokenize() lỗi: %s", e)

            # Nếu không lấy được kết quả thì coi như thất bại
            if not result:
                logger.warning("underthesea trả về rỗng/None cho văn bản: %r", text[:50])
                raise RuntimeError("underthesea không trả về kết quả")

            # Kết quả có thể là chuỗi hoặc danh sách
            if isinstance(result, str):
                tokens = result.split()
            else:
                tokens = list(result)
            
            # Loại bỏ token rỗng
            tokens = [t for t in tokens if t]
            # Nối từ ghép bằng dấu _
            tokens = [t.replace(" ", "_") for t in tokens]
            logger.debug("Tách được %d token bằng underthesea", len(tokens))
            return tokens
        except Exception as e:
            logger.warning("underthesea thất bại (%s), chuyển sang tách đơn giản", e)

    # Fallback: tách theo khoảng trắng
    if not _UNDER_AVAILABLE:
        logger.info("underthesea không có sẵn — sử dụng tách theo khoảng trắng đơn giản")
    return [tok for tok in text.split() if tok]


def preprocess_vietnamese(text: str) -> List[str]:
    """
    Quy trình tiền xử lý đầy đủ dành cho văn bản tiếng Việt
    
    Các bước:
    1. Chuẩn hóa văn bản (Unicode, chữ thường, khoảng trắng)
    2. Tách từ theo kiểu tiếng Việt
    
    Args:
        text: Văn bản tiếng Việt gốc
    
    Returns:
        Danh sách các token đã được tiền xử lý
    """
    # 1. Chuẩn hóa
    text = normalize_text(text)
    
    # 2. Tách từ
    tokens = vietnamese_tokenize(text)
    
    return tokens