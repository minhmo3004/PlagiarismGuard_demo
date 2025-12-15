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

router = APIRouter(prefix="/check", tags=["Plagiarism Check"])


@router.post("/upload", response_model=CheckUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload document and start plagiarism check
    
    - Validates file format and size
    - Checks user quota
    - Queues background job
    - Returns job_id for status polling
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
    
    # Validate file size (20MB max)
    # TODO: Read file size from upload
    # if file.size > 20 * 1024 * 1024:
    #     raise HTTPException(413, detail={"code": "FILE_TOO_LARGE"})
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # TODO: Save file to temp storage
    # file_path = await save_upload_file(file, job_id)
    
    # TODO: Create job record in database
    # await create_job(job_id, current_user.id, file.filename, file_path)
    
    # TODO: Queue background task
    # from app.workers.tasks import process_document
    # process_document.delay(job_id, file_path)
    
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
    Get job status for polling
    
    - Returns current status (pending, processing, done, failed)
    - Includes progress percentage if processing
    - Includes error message if failed
    """
    # TODO: Get job from database
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
    Get detailed check result
    
    - Only available when status = 'done'
    - Returns similarity scores and matched segments
    """
    # TODO: Get job and result from database
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
    Cancel a pending or processing job
    
    - Revokes Celery task
    - Updates status to 'cancelled'
    - Cleans up temp files
    """
    # TODO: Get job from database
    # job = await get_job(job_id)
    # if not job:
    #     raise HTTPException(404, detail={"code": "JOB_NOT_FOUND"})
    # if job.user_id != current_user.id:
    #     raise HTTPException(403, detail={"code": "FORBIDDEN"})
    # if job.status not in ["pending", "processing"]:
    #     raise HTTPException(400, detail={"code": "INVALID_JOB_STATUS"})
    
    # TODO: Revoke Celery task
    # from app.workers.celery_app import app
    # app.control.revoke(job.celery_task_id, terminate=True)
    
    # TODO: Update status
    # await update_job_status(job_id, {"status": "cancelled"})
    
    return {"status": "cancelled", "job_id": job_id}


@router.post("/{job_id}/retry", response_model=CheckUploadResponse)
async def retry_failed_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Retry a failed job
    
    - Only for jobs with status = 'failed' and can_retry = True
    - Checks quota again
    - Re-queues the job
    """
    # TODO: Get job from database
    # job = await get_job(job_id)
    # if not job:
    #     raise HTTPException(404, detail={"code": "JOB_NOT_FOUND"})
    # if job.user_id != current_user.id:
    #     raise HTTPException(403, detail={"code": "FORBIDDEN"})
    # if job.status != "failed":
    #     raise HTTPException(400, detail={"code": "INVALID_JOB_STATUS"})
    # if not job.can_retry:
    #     raise HTTPException(400, detail={"code": "CANNOT_RETRY"})
    
    # Check quota
    if not await check_user_quota(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "QUOTA_EXCEEDED"}
        )
    
    # TODO: Reset job status and re-queue
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
    Delete a job and its results
    
    - Removes job record
    - Cleans up files
    """
    # TODO: Get job and delete
    # job = await get_job(job_id)
    # if not job:
    #     raise HTTPException(404, detail={"code": "JOB_NOT_FOUND"})
    # if job.user_id != current_user.id:
    #     raise HTTPException(403, detail={"code": "FORBIDDEN"})
    
    # TODO: Delete job and cleanup
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
    Get user's check history
    
    - Returns list of jobs
    - Supports pagination
    """
    # TODO: Get jobs from database
    # jobs = await get_user_jobs(current_user.id, limit=limit, offset=offset)
    
    # Mock response
    return []
