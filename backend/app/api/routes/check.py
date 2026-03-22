"""
Các route kiểm tra đạo văn
Tải lên, trạng thái, kết quả, hủy, thử lại, lịch sử
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

from app.db.database import SessionLocal
from app.services.storage import S3Storage
from app.services.document_service import DocumentService
from app.workers.tasks import process_document

router = APIRouter(prefix="/check", tags=["Kiểm tra đạo văn"])


@router.post("/upload", response_model=CheckUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Tải lên tài liệu và bắt đầu kiểm tra đạo văn
    
    - Kiểm tra định dạng và kích thước file
    - Kiểm tra hạn mức (quota) của người dùng
    - Đưa công việc vào hàng đợi xử lý nền
    - Trả về job_id để theo dõi trạng thái
    """
    # Kiểm tra hạn mức sử dụng
    if not await check_user_quota(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "QUOTA_EXCEEDED",
                "message": "Bạn đã sử dụng hết lượt kiểm tra hôm nay"
            }
        )
    
    # Kiểm tra định dạng file
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
    
    # Kiểm tra kích thước file (tối đa 20MB)
    # TODO: Đọc kích thước file từ upload
    # if file.size > 20 * 1024 * 1024:
    #     raise HTTPException(413, detail={"code": "FILE_TOO_LARGE"})
    
    # Tạo ID cho job
    job_id = str(uuid.uuid4())

    # Đọc nội dung file
    content = await file.read()

    # Tính hash SHA256
    file_hash = DocumentService.compute_sha256(content)

    # Upload lên MinIO
    storage = S3Storage()
    object_name = f"uploads/{job_id}_{file.filename}"
    s3_path = storage.upload_bytes(content, object_name)

    # Lưu metadata tài liệu vào PostgreSQL
    db: Session = SessionLocal()
    try:
        doc = DocumentService.create_document(
            db,
            owner_id=current_user.id if hasattr(current_user, 'id') else None,
            original_filename=file.filename,
            s3_path=s3_path,
            file_hash=file_hash,
            file_size=len(content)
        )

        # Tạo bản ghi công việc kiểm tra trong DB (dùng job_id làm CheckResult.id)
        from app.db import models
        result = models.CheckResult(
            id=job_id,
            user_id=current_user.id if hasattr(current_user, 'id') else None,
            query_doc_id=doc.id,
            query_filename=file.filename,
            status='pending'
        )
        db.add(result)
        db.commit()

    finally:
        db.close()

    # Đưa vào hàng đợi xử lý nền bằng Celery
    try:
        process_document.delay(job_id, str(doc.id), file_ext)
    except Exception:
        # Nếu Celery chưa được cấu hình, bỏ qua và để trạng thái pending
        pass

    return CheckUploadResponse(
        job_id=job_id,
        status="pending",
        message="File đã được tải lên và đang chờ xử lý"
    )


@router.get("/status/{job_id}", response_model=JobStatus)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Lấy trạng thái công việc (dùng để polling)
    
    - Trả về trạng thái hiện tại (pending, processing, done, failed)
    - Bao gồm phần trăm tiến độ nếu đang xử lý
    - Bao gồm thông báo lỗi nếu thất bại
    """
    # TODO: Lấy thông tin job từ database
    # job = await get_job(job_id)
    # if not job:
    #     raise HTTPException(404, detail={"code": "JOB_NOT_FOUND"})
    # if job.user_id != current_user.id:
    #     raise HTTPException(403, detail={"code": "FORBIDDEN"})
    
    # Mock response
    return JobStatus(
        job_id=job_id,
        status="processing",
        progress=45,
        created_at=datetime.now()
    )


@router.get("/result/{job_id}", response_model=CheckResult)
async def get_check_result(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Lấy kết quả kiểm tra chi tiết
    
    - Chỉ khả dụng khi status = 'done'
    - Trả về điểm tương đồng và các đoạn khớp
    """
    # TODO: Lấy job và kết quả từ database
    # job = await get_job(job_id)
    # if not job:
    #     raise HTTPException(404, detail={"code": "JOB_NOT_FOUND"})
    # if job.user_id != current_user.id:
    #     raise HTTPException(403, detail={"code": "FORBIDDEN"})
    # if job.status != "done":
    #     raise HTTPException(400, detail={"code": "RESULT_NOT_READY"})
    
    # Mock response
    return CheckResult(
        job_id=job_id,
        status="done",
        query_filename="thesis.pdf",
        overall_similarity=0.42,
        match_count=3,
        matches=[],
        processing_time_ms=1250,
        created_at=datetime.now(),
        completed_at=datetime.now()
    )


@router.post("/{job_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Hủy công việc đang chờ hoặc đang xử lý
    
    - Thu hồi task Celery
    - Cập nhật trạng thái thành 'cancelled'
    - Dọn dẹp file tạm
    """
    # TODO: Lấy job từ database
    # job = await get_job(job_id)
    # if not job:
    #     raise HTTPException(404, detail={"code": "JOB_NOT_FOUND"})
    # if job.user_id != current_user.id:
    #     raise HTTPException(403, detail={"code": "FORBIDDEN"})
    # if job.status not in ["pending", "processing"]:
    #     raise HTTPException(400, detail={"code": "INVALID_JOB_STATUS"})
    
    # TODO: Thu hồi task Celery
    # from app.workers.celery_app import app
    # app.control.revoke(job.celery_task_id, terminate=True)
    
    # TODO: Cập nhật trạng thái
    # await update_job_status(job_id, {"status": "cancelled"})
    
    return {"status": "cancelled", "job_id": job_id}


@router.post("/{job_id}/retry", response_model=CheckUploadResponse)
async def retry_failed_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Thử lại công việc đã thất bại
    
    - Chỉ áp dụng cho job có status = 'failed' và can_retry = True
    - Kiểm tra lại quota
    - Đưa lại job vào hàng đợi
    """
    # TODO: Lấy job từ database
    # job = await get_job(job_id)
    # if not job:
    #     raise HTTPException(404, detail={"code": "JOB_NOT_FOUND"})
    # if job.user_id != current_user.id:
    #     raise HTTPException(403, detail={"code": "FORBIDDEN"})
    # if job.status != "failed":
    #     raise HTTPException(400, detail={"code": "INVALID_JOB_STATUS"})
    # if not job.can_retry:
    #     raise HTTPException(400, detail={"code": "CANNOT_RETRY"})
    
    # Kiểm tra quota
    if not await check_user_quota(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "QUOTA_EXCEEDED"}
        )
    
    # TODO: Reset trạng thái job và đưa lại vào hàng đợi
    # await update_job_status(job_id, {"status": "pending", "retry_count": 0})
    # process_document.delay(job_id, job.file_path)
    
    return CheckUploadResponse(
        job_id=job_id,
        status="pending",
        message="Job đã được đưa vào hàng đợi lại"
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Xóa công việc và kết quả liên quan
    
    - Xóa bản ghi công việc
    - Dọn dẹp các file liên quan
    """
    # TODO: Lấy job và xóa
    # job = await get_job(job_id)
    # if not job:
    #     raise HTTPException(404, detail={"code": "JOB_NOT_FOUND"})
    # if job.user_id != current_user.id:
    #     raise HTTPException(403, detail={"code": "FORBIDDEN"})
    
    # TODO: Xóa bản ghi và dọn dẹp file
    # await delete_job_record(job_id)
    # await cleanup_job_files(job_id)
    
    return None


@router.get("/history", response_model=List[JobStatus])
async def get_check_history(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Lấy lịch sử kiểm tra của người dùng
    
    - Trả về danh sách các công việc
    - Hỗ trợ phân trang (limit, offset)
    """
    # TODO: Lấy danh sách job từ database
    # jobs = await get_user_jobs(current_user.id, limit=limit, offset=offset)
    
    # Mock response
    return []