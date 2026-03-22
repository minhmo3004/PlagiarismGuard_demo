"""
Module trích xuất văn bản từ PDF
Hỗ trợ cả PDF thường và PDF dạng scan (sử dụng OCR)
"""
import fitz  # Thư viện PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import signal
from typing import Tuple
from .file_validator import is_scanned_pdf

# Cấu hình OCR
OCR_TIMEOUT_SECONDS = 300  # Timeout toàn bộ tài liệu: 5 phút
OCR_TIMEOUT_PER_PAGE = 30  # Timeout mỗi trang: 30 giây
MAX_PAGES_FOR_OCR = 100    # Giới hạn số trang khi dùng OCR


def filter_header_footer(page) -> str:
    """
    Loại bỏ header/footer dựa trên vị trí tọa độ
    
    Args:
        page: Đối tượng page của PyMuPDF
    
    Returns:
        Văn bản đã loại bỏ header/footer
    """
    page_height = page.rect.height
    
    # Vùng an toàn: bỏ 8% trên và dưới
    HEADER_THRESHOLD = page_height * 0.08
    FOOTER_THRESHOLD = page_height * 0.92
    
    safe_blocks = []
    for block in page.get_text("blocks"):
        x0, y0, x1, y1, text, block_no, block_type = block
        if y0 > HEADER_THRESHOLD and y1 < FOOTER_THRESHOLD:
            safe_blocks.append(text)
    
    return " ".join(safe_blocks)


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Trích xuất văn bản từ PDF (có loại bỏ header/footer)
    
    Args:
        pdf_path: Đường dẫn tới file PDF
    
    Returns:
        Văn bản đã trích xuất
    """
    doc = fitz.open(pdf_path)
    full_text = []
    
    for page in doc:
        text = filter_header_footer(page)
        full_text.append(text)
    
    doc.close()
    return "\n".join(full_text)


def ocr_pdf_with_timeout(pdf_path: str) -> str:
    """
    Thực hiện OCR với cơ chế giới hạn thời gian
    
    Args:
        pdf_path: Đường dẫn tới PDF dạng scan
    
    Returns:
        Văn bản trích xuất bằng OCR
    
    Raises:
        TimeoutError: Nếu OCR vượt quá thời gian cho phép
        ValueError: Nếu PDF có quá nhiều trang
    """
    def timeout_handler(signum, frame):
        raise TimeoutError("OCR vượt quá thời gian cho phép")
    
    # Thiết lập timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(OCR_TIMEOUT_SECONDS)
    
    try:
        images = convert_from_path(pdf_path)
        
        if len(images) > MAX_PAGES_FOR_OCR:
            raise ValueError(
                f"PDF có {len(images)} trang, vượt quá giới hạn {MAX_PAGES_FOR_OCR}"
            )
        
        full_text = []
        for i, image in enumerate(images):
            # Timeout cho từng trang
            text = pytesseract.image_to_string(
                image, 
                lang='vie+eng',
                timeout=OCR_TIMEOUT_PER_PAGE
            )
            full_text.append(text)
        
        return "\n".join(full_text)
    
    finally:
        signal.alarm(0)  # Hủy timeout


def extract_text_with_fallback(pdf_path: str) -> Tuple[str, str]:
    """
    Trích xuất văn bản với cơ chế fallback sang OCR
    
    Args:
        pdf_path: Đường dẫn tới file PDF
    
    Returns:
        Tuple gồm (text, phương pháp trích xuất)
        phương pháp: "ocr" hoặc "native"
    
    Raises:
        ValueError: Nếu không thể trích xuất
    """
    doc = fitz.open(pdf_path)
    
    # Kiểm tra trang đầu để xác định loại PDF
    first_page = doc[0]
    
    if is_scanned_pdf(first_page):
        doc.close()
        try:
            text = ocr_pdf_with_timeout(pdf_path)
            return text, "ocr"
        except TimeoutError:
            raise ValueError("OCR bị timeout - file quá lớn hoặc quá phức tạp")
        except Exception as e:
            raise ValueError(f"OCR thất bại: {str(e)}")
    else:
        text = "\n".join([filter_header_footer(page) for page in doc])
        doc.close()
        return text, "native"