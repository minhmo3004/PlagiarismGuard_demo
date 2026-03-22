"""
Các route API phát hiện đạo văn - PHIÊN BẢN ĐƠN GIẢN (Không yêu cầu xác thực)
2 Tính năng chính:
1. POST /compare - So sánh 2 file
2. POST /check - Kiểm tra 1 file với toàn bộ corpus
3. GET /history - Lịch sử kiểm tra
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from typing import List, Optional
import tempfile
import os
import redis
import json
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.plagiarism_checker import PlagiarismChecker
from app.config import settings
from app.db.database import get_db
from app.db.models import CheckResult, MatchDetail
from app.services.minio_storage import get_minio_storage

router = APIRouter(prefix="/plagiarism", tags=["Phát hiện đạo văn"])

# Instance checker toàn cục
_checker = None

def get_checker():
    global _checker
    if _checker is None:
        try:
            redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=False
            )
            redis_client.ping()
            _checker = PlagiarismChecker(redis_client)
        except:
            _checker = PlagiarismChecker(None)
    return _checker


# ═══════════════════════════════════════════════════════════════
# TÍNH NĂNG CHÍNH: Kiểm tra 1 file với toàn bộ corpus
# ═══════════════════════════════════════════════════════════════

@router.post("/check")
async def check_single_file(
    file: UploadFile = File(..., description="File cần kiểm tra"),
    db: Session = Depends(get_db)
):
    """
    Kiểm tra 1 file với toàn bộ corpus
    
    - Tải lên 1 file PDF/DOCX/TXT
    - So sánh với tất cả tài liệu trong corpus
    - Trả về danh sách các tài liệu có độ tương đồng
    
    Trả về:
        - is_plagiarized: True/False
        - overall_similarity: % tương đồng cao nhất
        - plagiarism_level: none/low/medium/high
        - matches: Danh sách tài liệu tương tự
        - word_count: Số từ trong file
        - processing_time_ms: Thời gian xử lý
    """
    # Kiểm tra định dạng file
    allowed = ['.pdf', '.docx', '.txt']
    ext = os.path.splitext(file.filename)[1].lower()
    
    if ext not in allowed:
        raise HTTPException(400, detail=f"Chỉ hỗ trợ: {allowed}")
    
    # Tạo ID duy nhất cho file
    file_id = str(uuid.uuid4())
    
    # Tạo thư mục tạm nếu chưa có
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    safe_filename = f"{file_id}_{file.filename}"
    local_file_path = os.path.join(upload_dir, safe_filename)
    
    try:
        # Lưu file tạm thời để xử lý
        content = await file.read()
        with open(local_file_path, 'wb') as f:
            f.write(content)
        
        checker = get_checker()
        result = checker.check_against_corpus(local_file_path, file.filename)
        
        # Upload lên MinIO để lưu trữ lâu dài
        minio_path = None
        minio_storage = get_minio_storage()
        if minio_storage.is_available():
            minio_path = minio_storage.upload_file(
                local_file_path,
                object_name=f"checks/{file_id}/{file.filename}"
            )
            if minio_path:
                # Xóa file cục bộ sau khi upload thành công lên MinIO
                os.unlink(local_file_path)
                local_file_path = None
        
        # Lưu kết quả vào PostgreSQL
        try:
            # Tạo bản ghi CheckResult
            check_result = CheckResult(
                id=uuid.UUID(file_id),
                query_filename=file.filename,
                overall_similarity=result.overall_similarity,
                plagiarism_level=result.plagiarism_level,
                match_count=len(result.matches),
                word_count=result.word_count,
                processing_time_ms=result.processing_time_ms,
                file_path=minio_path or local_file_path,  # Lưu đường dẫn MinIO hoặc cục bộ
                status='completed',
                completed_at=datetime.utcnow()
            )
            db.add(check_result)
            
            # Tạo các bản ghi MatchDetail cho từng đoạn khớp
            for m in result.matches:
                match_detail = MatchDetail(
                    result_id=uuid.UUID(file_id),
                    similarity_score=m.similarity,
                    source_title=m.title,
                    source_author=m.author,
                    source_university=m.university,
                    source_year=m.year,
                    matched_segments=json.dumps([
                        {
                            "query_text": seg.query_text,
                            "query_start": seg.query_start,
                            "query_end": seg.query_end,
                            "source_text": seg.source_text,
                            "source_start": seg.source_start,
                            "source_end": seg.source_end
                        }
                        for seg in (m.matched_segments or [])
                    ]) if m.matched_segments else None
                )
                db.add(match_detail)
            
            db.commit()
        except Exception as db_error:
            db.rollback()
            print(f"Lỗi lưu database: {db_error}")
        
        response = {
            "id": file_id,  # Trả về ID để frontend tham chiếu
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
                    "similarity": round(m.similarity * 100, 2),
                    "matched_segments": [
                        {
                            "query_text": seg.query_text,
                            "query_start": seg.query_start,
                            "query_end": seg.query_end,
                            "source_text": seg.source_text,
                            "source_start": seg.source_start,
                            "source_end": seg.source_end
                        }
                        for seg in (m.matched_segments or [])
                    ] if m.matched_segments else []
                }
                for m in result.matches
            ]
        }
        
        return response
    except Exception as e:
        # Dọn dẹp file cục bộ nếu xử lý thất bại
        if local_file_path and os.path.exists(local_file_path):
            os.unlink(local_file_path)
        raise


# ═══════════════════════════════════════════════════════════════
# THÔNG TIN CORPUS
# ═══════════════════════════════════════════════════════════════

@router.get("/corpus/stats")
async def get_corpus_stats():
    """Lấy thống kê corpus"""
    checker = get_checker()
    stats = checker.get_corpus_stats()
    return {
        "total_documents": stats["total_documents"],
        "threshold": stats["threshold"],
        "status": "ready" if stats["total_documents"] > 0 else "empty"
    }


# ═══════════════════════════════════════════════════════════════
# LỊCH SỬ KIỂM TRA (PostgreSQL)
# ═══════════════════════════════════════════════════════════════

@router.get("/history")
async def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Lấy lịch sử kiểm tra đạo văn từ PostgreSQL
    """
    try:
        # Tính offset
        offset = (page - 1) * page_size
        
        # Lấy tổng số bản ghi
        total = db.query(CheckResult).count()
        results = db.query(CheckResult)\
            .order_by(CheckResult.created_at.desc())\
            .offset(offset)\
            .limit(page_size)\
            .all()
        
        items = []
        for r in results:
            items.append({
                "id": str(r.id),
                "query_name": r.query_filename,
                "overall_similarity": float(r.overall_similarity * 100) if r.overall_similarity else 0,
                "matches_count": r.match_count or 0,
                "plagiarism_level": r.plagiarism_level,
                "file_path": r.file_path,
                "word_count": r.word_count,
                "processing_time_ms": r.processing_time_ms,
                "created_at": r.created_at.isoformat() if r.created_at else None
            })
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    except Exception as e:
        print(f"Lỗi lấy lịch sử: {e}")
        return {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size
        }


@router.get("/history/{item_id}")
async def get_history_detail(item_id: str, db: Session = Depends(get_db)):
    """Lấy chi tiết một mục lịch sử cùng với thông tin các đoạn khớp"""
    try:
        result = db.query(CheckResult).filter(CheckResult.id == uuid.UUID(item_id)).first()
        if not result:
            raise HTTPException(404, detail="Không tìm thấy mục lịch sử")
        
        # Lấy chi tiết các đoạn khớp
        matches = []
        for md in result.match_details:
            match_data = {
                "title": md.source_title,
                "author": md.source_author,
                "university": md.source_university,
                "year": md.source_year,
                "similarity": float(md.similarity_score * 100) if md.similarity_score else 0,
                "matched_segments": json.loads(md.matched_segments) if md.matched_segments else []
            }
            matches.append(match_data)
        
        return {
            "id": str(result.id),
            "filename": result.query_filename,
            "overall_similarity": float(result.overall_similarity * 100) if result.overall_similarity else 0,
            "plagiarism_level": result.plagiarism_level,
            "word_count": result.word_count,
            "processing_time_ms": result.processing_time_ms,
            "match_count": result.match_count,
            "created_at": result.created_at.isoformat() if result.created_at else None,
            "matches": matches
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.delete("/history/{item_id}")
async def delete_history_item(item_id: str, db: Session = Depends(get_db)):
    """Xóa một mục lịch sử đơn lẻ"""
    try:
        result = db.query(CheckResult).filter(CheckResult.id == uuid.UUID(item_id)).first()
        if not result:
            raise HTTPException(404, detail="Không tìm thấy mục lịch sử")
        
        # Xóa file liên quan - kiểm tra xem là đường dẫn MinIO hay cục bộ
        if result.file_path:
            if result.file_path.startswith('checks/'):
                # Đường dẫn MinIO
                minio_storage = get_minio_storage()
                if minio_storage.is_available():
                    minio_storage.delete_file(result.file_path)
            elif os.path.exists(result.file_path):
                # Đường dẫn cục bộ
                os.unlink(result.file_path)
        
        db.delete(result)
        db.commit()
        
        return {"message": "Đã xóa mục lịch sử"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, detail=str(e))


@router.get("/history/{item_id}/download")
async def download_history_file(item_id: str, db: Session = Depends(get_db)):
    """Tải xuống file gốc từ lịch sử kiểm tra"""
    from fastapi.responses import FileResponse, StreamingResponse
    from io import BytesIO
    
    try:
        result = db.query(CheckResult).filter(CheckResult.id == uuid.UUID(item_id)).first()
        if not result:
            raise HTTPException(404, detail="Không tìm thấy mục lịch sử")
        
        if not result.file_path:
            raise HTTPException(404, detail="Không có file liên quan đến lần kiểm tra này")
        
        # Kiểm tra xem là đường dẫn MinIO
        if result.file_path.startswith('checks/'):
            minio_storage = get_minio_storage()
            if minio_storage.is_available():
                file_data = minio_storage.download_file(result.file_path)
                if file_data:
                    return StreamingResponse(
                        BytesIO(file_data),
                        media_type='application/octet-stream',
                        headers={
                            'Content-Disposition': f'attachment; filename="{result.query_filename or "document.txt"}"'
                        }
                    )
            raise HTTPException(404, detail="Không tìm thấy file trong MinIO")
        
        # Đường dẫn file cục bộ
        if os.path.exists(result.file_path):
            return FileResponse(
                path=result.file_path,
                filename=result.query_filename or 'document.txt',
                media_type='application/octet-stream'
            )
        else:
            raise HTTPException(404, detail="File không còn tồn tại trên server.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.delete("/history")
async def clear_history(db: Session = Depends(get_db)):
    """Xóa toàn bộ lịch sử kiểm tra"""
    try:
        # Lấy tất cả bản ghi để xóa file
        results = db.query(CheckResult).all()
        minio_storage = get_minio_storage()
        
        for r in results:
            if r.file_path:
                try:
                    if r.file_path.startswith('checks/'):
                        # Đường dẫn MinIO
                        if minio_storage.is_available():
                            minio_storage.delete_file(r.file_path)
                    elif os.path.exists(r.file_path):
                        # Đường dẫn cục bộ
                        os.unlink(r.file_path)
                except:
                    pass
        
        # Xóa tất cả bản ghi (MatchDetails sẽ tự động xóa theo cascade)
        db.query(CheckResult).delete()
        db.commit()
        return {"message": "Đã xóa toàn bộ lịch sử"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, detail=str(e))