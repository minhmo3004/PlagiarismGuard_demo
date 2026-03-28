"""
Plagiarism check routes
Upload, status, result, cancel, retry, history
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from app.api.schemas import CheckUploadResponse, JobStatus, CheckResult
from app.api.deps import get_current_user, check_user_quota
from app.models.user import User
from typing import List
import uuid
from datetime import datetime
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import models
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
import json

router = APIRouter(prefix="/check", tags=["Plagiarism Check Pro"])


@router.post("/upload", response_model=CheckUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload document and start plagiarism check (Asynchronous Pro Flow)
    """
    # Check quota
    if not await check_user_quota(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "QUOTA_EXCEEDED",
                "message": "Bạn đã sử dụng hết lượt kiểm tra hôm nay"
            }
        )
    
    # Validate file format
    allowed_extensions = [".pdf", ".docx", ".txt", ".tex"]
    file_ext = "." + file.filename.split(".")[-1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_FILE_FORMAT",
                "message": "Định dạng file không được hỗ trợ"
            }
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())

    # Read binary content
    content = await file.read()
    file_hash = DocumentService.compute_sha256(content)

    # Upload to MinIO via consolidated storage
    storage = S3Storage()
    object_name = f"uploads/{job_id}_{file.filename}"
    s3_path = storage.upload_bytes(content, object_name)

    # Save to DB
    db: Session = SessionLocal()
    try:
        doc = DocumentService.create_document(
            db,
            owner_id=current_user.id,
            original_filename=file.filename,
            s3_path=s3_path,
            file_hash=file_hash,
            file_size=len(content)
        )

        # Create check job record
        result = models.CheckResult(
            id=uuid.UUID(job_id),
            user_id=current_user.id,
            query_doc_id=doc.id,
            query_filename=file.filename,
            status='pending',
            file_path=object_name # Store relative path for MinIO
        )
        db.add(result)
        
        # Increment user usage count
        db_user = db.query(models.User).filter(models.User.id == current_user.id).first()
        if db_user:
            db_user.daily_checks += 1
            
        db.commit()

        # Queue Celery task
        try:
            process_document.delay(job_id, str(doc.id), file_ext)
        except Exception as e:
            # If Celery isn't running, we at least have the record in DB
            print(f"⚠️ Celery Error: {e}")

        return CheckUploadResponse(
            job_id=job_id,
            status="pending",
            message="File đã được tải lên và đang được xử lý trong hàng đợi"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(500, detail=str(e))
    finally:
        db.close()


@router.get("/status/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get job status for polling
    """
    db = SessionLocal()
    try:
        job = db.query(models.CheckResult).filter(
            models.CheckResult.id == uuid.UUID(job_id),
            models.CheckResult.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(404, detail="Job not found")
            
        return {
            "job_id": job_id,
            "status": job.status,
            "overall_similarity": float(job.overall_similarity or 0),
            "created_at": job.created_at,
            "completed_at": job.completed_at
        }
    finally:
        db.close()


@router.get("/result/{job_id}", response_model=CheckResult)
async def get_check_result(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed check result (when status = 'done')
    """
    db = SessionLocal()
    try:
        job = db.query(models.CheckResult).filter(
            models.CheckResult.id == uuid.UUID(job_id),
            models.CheckResult.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(404, detail="Job not found")
            
        if job.status != "done":
            raise HTTPException(400, detail="Result not ready or job failed")
        
        # Format matches from match_details table
        matches = []
        details = db.query(models.MatchDetail).filter(models.MatchDetail.result_id == job.id).all()
        
        for detail in details:
            matches.append({
                "doc_id": str(detail.source_doc_id),
                "title": detail.source_title,
                "author": detail.source_author,
                "university": detail.source_university,
                "year": detail.source_year,
                "similarity": float(detail.similarity_score),
                "matched_segments": json.loads(detail.matched_segments) if detail.matched_segments else []
            })
            
        return CheckResult(
            job_id=job_id,
            status=job.status,
            query_filename=job.query_filename,
            overall_similarity=float(job.overall_similarity or 0),
            match_count=job.match_count,
            matches=matches,
            processing_time_ms=job.processing_time_ms or 0,
            created_at=job.created_at,
            completed_at=job.completed_at
        )
    finally:
        db.close()


@router.get("/history", response_model=List[JobStatus])
async def get_check_history(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get user's check history from database
    """
    db = SessionLocal()
    try:
        jobs = db.query(models.CheckResult).filter(
            models.CheckResult.user_id == current_user.id
        ).order_by(models.CheckResult.created_at.desc()).offset(offset).limit(limit).all()
        
        return [
            JobStatus(
                job_id=str(job.id),
                status=job.status,
                created_at=job.created_at
            ) for job in jobs
        ]
    finally:
        db.close()
