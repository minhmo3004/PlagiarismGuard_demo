"""
PDF text extraction module
Handles both native PDF and scanned PDF (with OCR)
"""
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import signal
from typing import Tuple
from .file_validator import is_scanned_pdf

# OCR Configuration
OCR_TIMEOUT_SECONDS = 300  # 5 phút timeout cho toàn bộ document
OCR_TIMEOUT_PER_PAGE = 30  # 30 giây per page
MAX_PAGES_FOR_OCR = 100    # Giới hạn số trang OCR


def filter_header_footer(page) -> str:
    """
    Loại bỏ header/footer dựa trên vị trí tọa độ
    
    Args:
        page: PyMuPDF page object
    
    Returns:
        Text without header/footer
    """
    page_height = page.rect.height
    
    # Safe zone: 8% từ trên và dưới
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
    Extract text từ PDF với header/footer removal
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        Extracted text
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
    OCR với timeout protection
    
    Args:
        pdf_path: Path to scanned PDF
    
    Returns:
        OCR extracted text
    
    Raises:
        TimeoutError: If OCR exceeds timeout
        ValueError: If PDF has too many pages
    """
    def timeout_handler(signum, frame):
        raise TimeoutError("OCR timeout exceeded")
    
    # Set timeout
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
            # Per-page timeout
            text = pytesseract.image_to_string(
                image, 
                lang='vie+eng',
                timeout=OCR_TIMEOUT_PER_PAGE
            )
            full_text.append(text)
        
        return "\n".join(full_text)
    
    finally:
        signal.alarm(0)  # Cancel timeout


def extract_text_with_fallback(pdf_path: str) -> Tuple[str, str]:
    """
    Extract text với OCR fallback
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        Tuple of (text, extraction_method)
        extraction_method: "ocr" or "native"
    
    Raises:
        ValueError: If extraction fails
    """
    doc = fitz.open(pdf_path)
    
    # Check first page to determine type
    first_page = doc[0]
    
    if is_scanned_pdf(first_page):
        doc.close()
        try:
            text = ocr_pdf_with_timeout(pdf_path)
            return text, "ocr"
        except TimeoutError:
            raise ValueError("OCR timeout - file quá lớn hoặc quá phức tạp")
        except Exception as e:
            raise ValueError(f"OCR failed: {str(e)}")
    else:
        text = "\n".join([filter_header_footer(page) for page in doc])
        doc.close()
        return text, "native"
