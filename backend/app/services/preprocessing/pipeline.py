"""
Preprocessing pipeline - Main entry point
Orchestrates all preprocessing steps
"""
from typing import Tuple, Dict, List
from .file_validator import validate_pdf, FileValidationError
from .pdf_extractor import extract_text_with_fallback
from .vietnamese_nlp import preprocess_vietnamese
import docx  # python-docx
import re


def extract_docx(file_path: str) -> str:
    """
    Extract text from DOCX file
    
    Args:
        file_path: Path to DOCX file
    
    Returns:
        Extracted text
    """
    doc = docx.Document(file_path)
    full_text = []
    
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)
    
    return "\n".join(full_text)


def strip_latex_commands(text: str) -> str:
    """
    Loại bỏ LaTeX commands, giữ lại nội dung text
    
    Args:
        text: LaTeX source code
    
    Returns:
        Text without LaTeX commands
    """
    # Remove comments
    text = re.sub(r'%.*$', '', text, flags=re.MULTILINE)
    
    # Remove \command{} but keep content
    text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
    
    # Remove standalone commands
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    
    # Remove math blocks, replace with token
    text = re.sub(r'\$\$.*?\$\$', ' <EQUATION> ', text, flags=re.DOTALL)
    text = re.sub(r'\$.*?\$', ' <EQUATION> ', text)
    
    # Remove braces
    text = re.sub(r'[{}]', '', text)
    
    return text


class PreprocessingPipeline:
    """Main entry point cho preprocessing"""
    
    def __init__(self):
        self.supported_formats = ['pdf', 'docx', 'txt', 'tex']
    
    def process(self, file_path: str, file_type: str) -> Tuple[List[str], Dict]:
        """
        Process file và trả về tokens
        
        Args:
            file_path: Path to file
            file_type: File extension (pdf, docx, txt, tex)
        
        Returns:
            Tuple of:
                - tokens: List các từ đã tokenize
                - metadata: Dict chứa thông tin extraction
        
        Raises:
            ValueError: If file type not supported
            FileValidationError: If file validation fails
        """
        metadata = {"file_type": file_type, "method": None}
        
        if file_type == 'pdf':
            # Validate first
            validation = validate_pdf(file_path)
            metadata["page_count"] = validation["page_count"]
            metadata["is_scanned"] = validation["is_scanned"]
            
            # Extract text
            text, method = extract_text_with_fallback(file_path)
            metadata["method"] = method
            
        elif file_type == 'docx':
            text = extract_docx(file_path)
            metadata["method"] = "python-docx"
            
        elif file_type == 'tex':
            with open(file_path, 'r', encoding='utf-8') as f:
                raw = f.read()
            text = strip_latex_commands(raw)
            metadata["method"] = "latex-strip"
            
        elif file_type == 'txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            metadata["method"] = "direct"
        
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Normalize and tokenize
        tokens = preprocess_vietnamese(text)
        metadata["token_count"] = len(tokens)
        
        return tokens, metadata
