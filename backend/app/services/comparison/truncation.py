"""
Truncation module for diff results
Prevents response size from becoming too large
"""
from typing import Dict, List

# Limits to prevent response overflow
MAX_SEGMENT_TEXT_LENGTH = 500      # Chars per segment text
MAX_TOTAL_SEGMENTS = 100           # Total segments in response
MAX_RESPONSE_SIZE_BYTES = 1_000_000  # 1MB max response


def truncate_segment_text(
    segment: Dict, 
    max_length: int = MAX_SEGMENT_TEXT_LENGTH
) -> Dict:
    """
    Truncate text trong segment nếu quá dài
    
    Args:
        segment: Segment dict with source_text and query_text
        max_length: Maximum character length for text fields
    
    Returns:
        Segment dict with truncated text if necessary
    
    Example:
        segment = {"source_text": "very long text...", ...}
        truncated = truncate_segment_text(segment, max_length=100)
        # truncated["source_text"] = "very long text... [truncated]"
        # truncated["source_text_truncated"] = True
    """
    segment = segment.copy()
    
    for key in ["source_text", "query_text"]:
        if key in segment and len(segment[key]) > max_length:
            segment[key] = segment[key][:max_length] + "... [truncated]"
            segment[f"{key}_truncated"] = True
        else:
            segment[f"{key}_truncated"] = False
    
    return segment


def truncate_diff_result(result: Dict) -> Dict:
    """
    Truncate toàn bộ diff result cho API response
    
    Applies two levels of truncation:
    1. Limits total number of segments
    2. Truncates text within each segment
    
    Args:
        result: Full diff result dict
    
    Returns:
        Truncated diff result
    
    Example:
        result = {"segments": [...200 segments...], ...}
        truncated = truncate_diff_result(result)
        # truncated["segments"] has max 100 segments
        # Each segment text is max 500 chars
    """
    result = result.copy()
    
    # Limit number of segments
    if len(result.get("segments", [])) > MAX_TOTAL_SEGMENTS:
        original_count = len(result["segments"])
        result["segments"] = result["segments"][:MAX_TOTAL_SEGMENTS]
        result["segments_truncated"] = True
        result["total_segments_before_truncation"] = original_count
    else:
        result["segments_truncated"] = False
    
    # Truncate each segment's text
    result["segments"] = [
        truncate_segment_text(seg) for seg in result.get("segments", [])
    ]
    
    return result


def estimate_response_size(result: Dict) -> int:
    """
    Estimate response size in bytes
    
    Args:
        result: Diff result dict
    
    Returns:
        Estimated size in bytes
    """
    import json
    return len(json.dumps(result).encode('utf-8'))
