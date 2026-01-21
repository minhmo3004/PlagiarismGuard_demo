"""
Plagiarism API routes - SIMPLE VERSION (No Auth)
2 Features:
1. POST /compare - So sánh 2 files
2. POST /check - Check 1 file với corpus
3. GET /history - Lịch sử kiểm tra
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import List, Optional
import tempfile
import os
import redis
import json
import uuid
from datetime import datetime

from app.services.plagiarism_checker import PlagiarismChecker
from app.config import settings

router = APIRouter(prefix="/plagiarism", tags=["Plagiarism Detection"])

# Global checker instance
_checker = None

def get_checker():
    global _checker
    if _checker is None:
        try:
            redis_client = redis.Redis(
                host='localhost', 
                port=6379, 
                db=0,
                decode_responses=False
            )
            redis_client.ping()
            _checker = PlagiarismChecker(redis_client)
        except:
            _checker = PlagiarismChecker(None)
    return _checker



# ═══════════════════════════════════════════════════════════════
# FEATURE chính: Check 1 file với corpus
# ═══════════════════════════════════════════════════════════════

@router.post("/check")
async def check_single_file(
    file: UploadFile = File(..., description="File cần kiểm tra")
):
    """
    Check 1 file với corpus
    
    - Upload 1 file PDF/DOCX/TXT
    - So sánh với tất cả documents trong corpus
    - Trả về danh sách các documents tương tự
    
    Returns:
        - is_plagiarized: True/False
        - overall_similarity: % tương đồng cao nhất
        - plagiarism_level: none/low/medium/high
        - matches: Danh sách tài liệu tương tự
        - word_count: Số từ trong file
        - processing_time_ms: Thời gian xử lý
    """
    # Validate
    allowed = ['.pdf', '.docx', '.txt']
    ext = os.path.splitext(file.filename)[1].lower()
    
    if ext not in allowed:
        raise HTTPException(400, detail=f"Chỉ hỗ trợ: {allowed}")
    
    
    # Save file permanently in uploads/ directory
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(upload_dir, safe_filename)
    
    try:
        # Save file
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        checker = get_checker()
        result = checker.check_against_corpus(file_path, file.filename)
        
        response = {
            "filename": file.filename,
            "is_plagiarized": result.is_plagiarized,
            "overall_similarity": round(result.overall_similarity * 100, 2),
            "plagiarism_level": result.plagiarism_level,
            "word_count": result.word_count,
            "processing_time_ms": result.processing_time_ms,
            "corpus_size": checker.get_corpus_stats()["total_documents"],
            "matches": [
                {
                    "title": m.title,
                    "author": m.author,
                    "university": m.university,
                    "year": m.year,
                    "similarity": round(m.similarity * 100, 2)
                }
                for m in result.matches
            ]
        }
        
        # Save to history in Redis with file path
        try:
            r = redis.Redis(host='localhost', port=6379, db=0)
            history_item = {
                "id": file_id,  # Use same ID for consistency
                "query_name": file.filename,
                "overall_similarity": round(result.overall_similarity * 100, 2),
                "matches_count": len(result.matches),
                "plagiarism_level": result.plagiarism_level,
                "file_path": file_path,  # Save file path for download
                "created_at": datetime.now().isoformat()
            }
            r.lpush("check:history", json.dumps(history_item))
            r.ltrim("check:history", 0, 99)  # Keep last 100
        except:
            pass  # Ignore history save errors
        
        return response
    except Exception as e:
        # Clean up file if processing failed
        if os.path.exists(file_path):
            os.unlink(file_path)
        raise


# ═══════════════════════════════════════════════════════════════
# CORPUS INFO
# ═══════════════════════════════════════════════════════════════

@router.get("/corpus/stats")
async def get_corpus_stats():
    """Get corpus statistics"""
    checker = get_checker()
    stats = checker.get_corpus_stats()
    return {
        "total_documents": stats["total_documents"],
        "threshold": stats["threshold"],
        "status": "ready" if stats["total_documents"] > 0 else "empty"
    }


# ═══════════════════════════════════════════════════════════════
# HISTORY
# ═══════════════════════════════════════════════════════════════

@router.get("/history")
async def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50)
):
    """
    Get plagiarism check history
    """
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # Get items with pagination
        start = (page - 1) * page_size
        end = start + page_size - 1
        
        items_raw = r.lrange("check:history", start, end)
        total = r.llen("check:history")
        
        items = []
        for item in items_raw:
            try:
                if isinstance(item, bytes):
                    item = item.decode()
                items.append(json.loads(item))
            except:
                continue
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    except Exception as e:
        return {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size
        }


@router.delete("/history/{item_id}")
async def delete_history_item(item_id: str):
    """Delete a single history item"""
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # Get all history items
        items_raw = r.lrange("check:history", 0, -1)
        
        # Filter out the item to delete
        new_items = []
        deleted = False
        for item in items_raw:
            try:
                if isinstance(item, bytes):
                    item = item.decode()
                item_data = json.loads(item)
                if item_data.get('id') != item_id:
                    new_items.append(item)
                else:
                    deleted = True
            except:
                continue
        
        if not deleted:
            raise HTTPException(404, detail="History item not found")
        
        # Replace the list
        r.delete("check:history")
        if new_items:
            for item in new_items:
                r.rpush("check:history", item)
        
        return {"message": "History item deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/history/{item_id}/download")
async def download_history_file(item_id: str):
    """Download the original file from history"""
    from fastapi.responses import FileResponse
    
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # Find the history item
        items_raw = r.lrange("check:history", 0, -1)
        
        for item in items_raw:
            try:
                if isinstance(item, bytes):
                    item = item.decode()
                item_data = json.loads(item)
                
                if item_data.get('id') == item_id:
                    filename = item_data.get('query_name', 'document.txt')
                    file_path = item_data.get('file_path')
                    
                    # If file path exists and file still exists
                    if file_path and os.path.exists(file_path):
                        return FileResponse(
                            path=file_path,
                            filename=filename,
                            media_type='application/octet-stream'
                        )
                    else:
                        raise HTTPException(
                            404, 
                            detail="File no longer exists. Files are automatically deleted after processing."
                        )
            except json.JSONDecodeError:
                continue
        
        raise HTTPException(404, detail="History item not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.delete("/history")
async def clear_history():
    """Clear all history"""
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.delete("check:history")
        return {"message": "History cleared"}
    except Exception as e:
        raise HTTPException(500, detail=str(e))
