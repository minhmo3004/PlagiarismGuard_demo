"""
Pipeline tiền xử lý - Điểm vào chính của hệ thống
Điều phối toàn bộ các bước tiền xử lý
"""
from typing import Tuple, Dict, List
from .file_validator import validate_pdf, FileValidationError
from .pdf_extractor import extract_text_with_fallback
from .vietnamese_nlp import preprocess_vietnamese
import docx  # Thư viện python-docx
import re


def extract_docx(file_path: str) -> str:
    """
    Trích xuất văn bản từ file DOCX
    
    Args:
        file_path: Đường dẫn tới file DOCX
    
    Returns:
        Văn bản đã trích xuất
    """
    doc = docx.Document(file_path)
    full_text = []
    
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)
    
    return "\n".join(full_text)


def strip_latex_commands(text: str) -> str:
    """
    Loại bỏ các lệnh LaTeX, giữ lại nội dung văn bản
    
    Args:
        text: Mã nguồn LaTeX
    
    Returns:
        Văn bản đã loại bỏ lệnh LaTeX
    """
    # Xóa comment trong LaTeX
    text = re.sub(r'%.*$', '', text, flags=re.MULTILINE)
    
    # Xóa \command{} nhưng giữ lại nội dung bên trong
    text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
    
    # Xóa các lệnh standalone (không có {})
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    
    # Xóa block công thức toán, thay bằng token
    text = re.sub(r'\$\$.*?\$\$', ' <EQUATION> ', text, flags=re.DOTALL)
    text = re.sub(r'\$.*?\$', ' <EQUATION> ', text)
    
    # Xóa dấu ngoặc {}
    text = re.sub(r'[{}]', '', text)
    
    return text


class PreprocessingPipeline:
    """Điểm vào chính của module tiền xử lý"""
    
    def __init__(self):
        self.supported_formats = ['pdf', 'docx', 'txt', 'tex']
    
    def process(self, file_path: str, file_type: str) -> Tuple[List[str], Dict]:
        """
        Xử lý file và trả về tokens
        
        Args:
            file_path: Đường dẫn tới file
            file_type: Loại file (pdf, docx, txt, tex)
        
        Returns:
            Tuple gồm:
                - tokens: Danh sách các từ đã tokenize
                - metadata: Dict chứa thông tin trích xuất
        
        Raises:
            ValueError: Nếu định dạng file không được hỗ trợ
            FileValidationError: Nếu file không hợp lệ
        """
        metadata = {"file_type": file_type, "method": None}
        
        if file_type == 'pdf':
            # Bước 1: Xác thực file
            validation = validate_pdf(file_path)
            metadata["page_count"] = validation["page_count"]
            metadata["is_scanned"] = validation["is_scanned"]
            
            # Bước 2: Trích xuất văn bản
            text, method = extract_text_with_fallback(file_path)
            metadata["method"] = method
            
        elif file_type == 'docx':
            text = extract_docx(file_path)
            metadata["method"] = "python-docx"
            
        elif file_type == 'tex':
            with open(file_path, 'r', encoding='utf-8') as f:
                raw = f.read()
            text = strip_latex_commands(raw)
            metadata["method"] = "latex-loại-bỏ"
            
        elif file_type == 'txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            metadata["method"] = "đọc-trực-tiếp"
        
        else:
            raise ValueError(f"Định dạng file không hỗ trợ: {file_type}")
        
        # Chuẩn hóa và tokenize tiếng Việt
        tokens = preprocess_vietnamese(text)
        metadata["token_count"] = len(tokens)
        
        return tokens, metadata