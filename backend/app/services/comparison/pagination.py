"""
Pagination module for diff results
Handles pagination for large diff results
"""
from dataclasses import dataclass
from typing import List, Dict
from .diff_engine import DiffEngine


@dataclass
class PaginatedDiffResult:
    """Kết quả diff với pagination"""
    total_segments: int
    page: int
    page_size: int
    total_pages: int
    segments: List[Dict]
    has_next: bool
    has_prev: bool
    similarity: float


class PaginatedDiffEngine:
    """
    Diff engine với pagination support
    
    For documents with many matching segments, pagination prevents
    overwhelming the client with too much data at once.
    """
    
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 50
    
    def __init__(self, diff_engine: DiffEngine = None):
        """
        Initialize paginated diff engine
        
        Args:
            diff_engine: DiffEngine instance (creates new if None)
        """
        self.diff_engine = diff_engine or DiffEngine()
    
    def compare_paginated(
        self, 
        query_text: str, 
        source_text: str,
        page: int = 1,
        page_size: int = 10
    ) -> PaginatedDiffResult:
        """
        So sánh với pagination
        
        Args:
            query_text: Query document text
            source_text: Source document text
            page: 1-indexed page number
            page_size: Số segments per page (max 50)
        
        Returns:
            PaginatedDiffResult with segments for requested page
        
        Example:
            result = engine.compare_paginated(query, source, page=2, page_size=10)
            # Returns segments 11-20
        """
        # Enforce limits
        page_size = min(page_size, self.MAX_PAGE_SIZE)
        page = max(1, page)
        
        # Get full diff result
        full_result = self.diff_engine.compare(query_text, source_text)
        all_segments = full_result["segments"]
        similarity = full_result["similarity"]
        
        # Calculate pagination
        total = len(all_segments)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        # Slice segments for current page
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_segments = all_segments[start_idx:end_idx]
        
        return PaginatedDiffResult(
            total_segments=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            segments=page_segments,
            has_next=page < total_pages,
            has_prev=page > 1,
            similarity=similarity
        )
