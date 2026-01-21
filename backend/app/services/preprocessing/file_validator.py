"""
File validation module
Validates PDF files before processing
"""
import logging
import mimetypes

try:
    import magic
except Exception:
    magic = None

import fitz  # PyMuPDF
from typing import Dict


class FileValidationError(Exception):
    """Custom exception for file validation errors"""
    pass


def is_scanned_pdf(page) -> bool:
    """
    Phát hiện PDF là dạng scan (ảnh)
    
    Args:
        page: PyMuPDF page object
    
    Returns:
        True if page is scanned (image-based)
    """
    text = page.get_text()
    images = page.get_images()
    # Nếu ít text nhưng nhiều ảnh → scan
    return len(text.strip()) < 50 and len(images) > 0


def validate_pdf(file_path: str) -> Dict:
    """
    Validate PDF file trước khi xử lý
    
    Args:
        file_path: Path to PDF file
    
    Returns:
        dict với thông tin file
    
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
    
    # Try to open PDF first (PyMuPDF is reliable)
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        raise FileValidationError(f"Không thể mở PDF: {str(e)}")

    # If python-magic is available, validate MIME type as extra check
    if magic:
        try:
            mime = magic.from_file(file_path, mime=True)
            if mime != "application/pdf":
                doc.close()
                raise FileValidationError(f"File không phải PDF. Detected: {mime}")
        except Exception as e:
            doc.close()
            raise FileValidationError(f"Không thể kiểm tra MIME type: {str(e)}")
    else:
        logging.warning("python-magic not available; skipping MIME type check. Install 'python-magic-bin' on Windows or 'libmagic' on Linux for strict checks.")
    
    # Check encrypted
    if doc.is_encrypted:
        if not doc.authenticate(""):  # Try empty password
            raise FileValidationError("PDF được bảo vệ bằng mật khẩu")
    
    # Check page count
    if doc.page_count == 0:
        raise FileValidationError("PDF không có trang nào")
    
    if doc.page_count > 500:
        raise FileValidationError(
            f"PDF có {doc.page_count} trang, vượt quá giới hạn 500 trang"
        )
    
    # Check if readable
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
