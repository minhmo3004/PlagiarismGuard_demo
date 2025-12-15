"""
Diff Engine module
Deep comparison using difflib SequenceMatcher
"""
from difflib import SequenceMatcher
from typing import List, Dict, Any


class DiffEngine:
    """
    Engine so sánh chi tiết giữa 2 văn bản
    
    Uses Ratcliff/Obershelp algorithm (SequenceMatcher) to find
    matching blocks between two texts.
    """
    
    def __init__(self, min_match_length: int = 50):
        """
        Initialize diff engine
        
        Args:
            min_match_length: Minimum character length for a match (default 50)
        """
        self.min_match_length = min_match_length
    
    def compare(self, query_text: str, source_text: str) -> Dict[str, Any]:
        """
        So sánh 2 văn bản và trả về các đoạn trùng khớp
        
        Args:
            query_text: Văn bản cần kiểm tra
            source_text: Văn bản trong corpus
        
        Returns:
            Dict chứa similarity score và matched segments
        
        Example:
            result = diff_engine.compare(query, source)
            # result = {
            #     "similarity": 0.75,
            #     "segments": [...],
            #     "segment_count": 5
            # }
        """
        # Sử dụng SequenceMatcher với autojunk=False
        # autojunk=False ensures all words are considered
        matcher = SequenceMatcher(None, source_text, query_text, autojunk=False)
        
        # Overall ratio (0.0 to 1.0)
        similarity = matcher.ratio()
        
        # Find matching blocks
        segments = []
        for block in matcher.get_matching_blocks():
            if block.size >= self.min_match_length:
                segments.append({
                    "source_start": block.a,
                    "source_end": block.a + block.size,
                    "query_start": block.b,
                    "query_end": block.b + block.size,
                    "length": block.size,
                    "source_text": source_text[block.a:block.a + block.size],
                    "query_text": query_text[block.b:block.b + block.size]
                })
        
        return {
            "similarity": similarity,
            "segments": segments,
            "segment_count": len(segments)
        }
