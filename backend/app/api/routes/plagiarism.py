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
# FEATURE 1: So sánh 2 files với nhau
# ═══════════════════════════════════════════════════════════════

@router.post("/compare")
async def compare_two_files(
    file1: UploadFile = File(..., description="File thứ nhất"),
    file2: UploadFile = File(..., description="File thứ hai")
):
    """
    So sánh 2 files với nhau
    
    - Upload 2 files PDF/DOCX/TXT
    - Trả về % tương đồng giữa 2 files
    
    Returns:
        - similarity: % tương đồng (0-100)
        - is_similar: True nếu >= 40%
        - file1_word_count: Số từ file 1
        - file2_word_count: Số từ file 2
        - processing_time_ms: Thời gian xử lý (ms)
    """
    # Validate file types
    allowed = ['.pdf', '.docx', '.txt']
    ext1 = os.path.splitext(file1.filename)[1].lower()
    ext2 = os.path.splitext(file2.filename)[1].lower()
    
    if ext1 not in allowed or ext2 not in allowed:
        raise HTTPException(400, detail=f"Chỉ hỗ trợ: {allowed}")
    
    # Save to temp files
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext1) as tmp1:
        content1 = await file1.read()
        tmp1.write(content1)
        tmp1_path = tmp1.name
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext2) as tmp2:
        content2 = await file2.read()
        tmp2.write(content2)
        tmp2_path = tmp2.name
    
    try:
        checker = get_checker()
        result = checker.compare_two_files(
            tmp1_path, file1.filename,
            tmp2_path, file2.filename
        )
        
        return {
            "file1": file1.filename,
            "file2": file2.filename,
            "similarity": round(result.similarity * 100, 2),
            "is_similar": result.is_similar,
            "similarity_level": (
                "high" if result.similarity >= 0.7 else
                "medium" if result.similarity >= 0.4 else
                "low" if result.similarity >= 0.2 else
                "none"
            ),
            "file1_word_count": result.file1_word_count,
            "file2_word_count": result.file2_word_count,
            "processing_time_ms": result.processing_time_ms
        }
    finally:
        os.unlink(tmp1_path)
        os.unlink(tmp2_path)


# ═══════════════════════════════════════════════════════════════
# FEATURE 2: Check 1 file với corpus
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
    
    # Save temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        checker = get_checker()
        result = checker.check_against_corpus(tmp_path, file.filename)
        
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
        
        # Save to history in Redis
        try:
            r = redis.Redis(host='localhost', port=6379, db=0)
            history_item = {
                "id": str(uuid.uuid4()),
                "query_name": file.filename,
                "overall_similarity": round(result.overall_similarity * 100, 2),
                "matches_count": len(result.matches),
                "plagiarism_level": result.plagiarism_level,
                "created_at": datetime.now().isoformat()
            }
            r.lpush("check:history", json.dumps(history_item))
            r.ltrim("check:history", 0, 99)  # Keep last 100
        except:
            pass  # Ignore history save errors
        
        return response
    finally:
        os.unlink(tmp_path)


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


@router.delete("/history")
async def clear_history():
    """Clear all history"""
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.delete("check:history")
        return {"message": "History cleared"}
    except Exception as e:
        raise HTTPException(500, detail=str(e))
