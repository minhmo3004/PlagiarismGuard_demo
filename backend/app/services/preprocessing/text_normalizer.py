"""
Module chuẩn hóa văn bản
Xử lý chuẩn hóa Unicode, mở rộng ligature, chuyển về chữ thường
"""
import unicodedata
import re

# Bảng ánh xạ ligature để đảm bảo đồng nhất font
LIGATURE_MAP = {
    'ﬁ': 'fi', 'ﬂ': 'fl', 'ﬀ': 'ff', 
    'ﬃ': 'ffi', 'ﬄ': 'ffl', 'œ': 'oe', 'æ': 'ae'
}


def normalize_text(text: str) -> str:
    """
    Chuẩn hóa văn bản để sử dụng cho shingling
    
    Các bước thực hiện:
    1. Chuẩn hóa Unicode (NFKD)
    2. Mở rộng ligature
    3. Chuyển thành chữ thường
    4. Thu gọn nhiều khoảng trắng thành một
    5. Xóa khoảng trắng đầu/cuối
    
    Args:
        text: Chuỗi văn bản gốc
    
    Returns:
        Văn bản đã được chuẩn hóa
    """
    # 1. Chuẩn hóa Unicode (NFKD)
    # Phân tách ký tự: é → e + ´
    text = unicodedata.normalize('NFKD', text)
    
    # 2. Mở rộng ligature
    # Thay các ký tự ligature bằng các ký tự riêng lẻ
    for lig, replacement in LIGATURE_MAP.items():
        text = text.replace(lig, replacement)
    
    # 3. Chuyển thành chữ thường
    text = text.lower()
    
    # 4. Thu gọn khoảng trắng
    # Thay nhiều khoảng trắng liên tiếp bằng một khoảng trắng
    text = re.sub(r'\s+', ' ', text)
    
    # 5. Xóa khoảng trắng thừa đầu và cuối chuỗi
    text = text.strip()
    
    return text


def remove_vietnamese_tones(text: str) -> str:
    """
    Loại bỏ dấu thanh tiếng Việt (chỉ dùng khi cần so sánh đa ngôn ngữ)
    
    Lưu ý: 
    KHÔNG sử dụng hàm này cho corpus chỉ có tiếng Việt.
    Chỉ dùng khi cần so sánh văn bản tiếng Việt với tiếng Anh hoặc các ngôn ngữ không dấu.
    
    Args:
        text: Văn bản tiếng Việt có dấu
    
    Returns:
        Văn bản đã bỏ dấu thanh
    """
    # NFKD tách dấu ra khỏi chữ cái
    text = unicodedata.normalize('NFKD', text)
    
    # Loại bỏ tất cả ký tự dấu (combining marks)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    
    # Xử lý đặc biệt cho chữ đ/Đ
    text = text.replace('đ', 'd').replace('Đ', 'D')
    
    return text