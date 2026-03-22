"""
Module kiểm tra file
Xác thực file PDF trước khi xử lý
"""
import logging
import mimetypes

try:
    import magic
except Exception:
    magic = None

import fitz  # Thư viện PyMuPDF
from typing import Dict


class FileValidationError(Exception):
    """Ngoại lệ tùy chỉnh cho lỗi xác thực file"""
    pass


def is_scanned_pdf(page) -> bool:
    """
    Phát hiện PDF có phải dạng scan (ảnh) hay không
    
    Args:
        page: Đối tượng page của PyMuPDF
    
    Returns:
        True nếu trang là dạng scan (dựa trên ảnh)
    """
    text = page.get_text()
    images = page.get_images()
    # Nếu ít text nhưng có nhiều ảnh → khả năng là scan
    return len(text.strip()) < 50 and len(images) > 0


def validate_pdf(file_path: str) -> Dict:
    """
    Xác thực file PDF trước khi đưa vào xử lý
    
    Args:
        file_path: Đường dẫn tới file PDF
    
    Returns:
        dict chứa thông tin về file
    
    Raises:
        FileValidationError nếu file không hợp lệ
    """
    result = {
        "valid": False,
        "page_count": 0,
        "is_encrypted": False,
        "is_scanned": False,
        "error": None
    }
    
    # Thử mở file PDF trước (PyMuPDF khá ổn định)
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        raise FileValidationError(f"Không thể mở PDF: {str(e)}")

    # Nếu có python-magic thì kiểm tra MIME type để chắc chắn là PDF
    if magic:
        try:
            mime = magic.from_file(file_path, mime=True)
            if mime != "application/pdf":
                doc.close()
                raise FileValidationError(f"File không phải PDF. Phát hiện: {mime}")
        except Exception as e:
            doc.close()
            raise FileValidationError(f"Không thể kiểm tra MIME type: {str(e)}")
    else:
        logging.warning("Không có python-magic; bỏ qua kiểm tra MIME type. Cài 'python-magic-bin' (Windows) hoặc 'libmagic' (Linux) để kiểm tra chặt chẽ hơn.")
    
    # Kiểm tra file có bị mã hóa không
    if doc.is_encrypted:
        if not doc.authenticate(""):  # Thử password rỗng
            raise FileValidationError("PDF được bảo vệ bằng mật khẩu")
    
    # Kiểm tra số trang
    if doc.page_count == 0:
        raise FileValidationError("PDF không có trang nào")
    
    if doc.page_count > 500:
        raise FileValidationError(
            f"PDF có {doc.page_count} trang, vượt quá giới hạn 500 trang"
        )
    
    # Kiểm tra khả năng đọc nội dung
    total_text = ""
    for page in doc:
        total_text += page.get_text()
    
    if len(total_text.strip()) < 100 and not is_scanned_pdf(doc[0]):
        raise FileValidationError("PDF không có nội dung text có thể đọc được")
    
    result["valid"] = True
    result["page_count"] = doc.page_count
    result["is_scanned"] = is_scanned_pdf(doc[0])
    
    doc.close()
    return result