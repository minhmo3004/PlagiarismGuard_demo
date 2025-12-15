"""
Celery tasks for background processing
"""
from celery import Task
from celery.exceptions import MaxRetriesExceededError
from app.workers.celery_app import app
from app.services.algorithm.pipeline import PlagiarismPipeline
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Retry configuration
RETRY_DELAYS = [60, 300, 900]  # 1min, 5min, 15min
MAX_RETRIES = 3


class TransientError(Exception):
    """Temporary error that should be retried"""
    pass


class PermanentError(Exception):
    """Permanent error that should not be retried"""
    pass


@app.task(bind=True, max_retries=MAX_RETRIES)
def process_document(self: Task, job_id: str, file_path: str, file_type: str):
    """
    Process document for plagiarism check
    
    Steps:
    1. Validate file
    2. Extract text
    3. Preprocess (Vietnamese NLP)
    4. Create shingles
    5. Create MinHash
    6. Query LSH
    7. Deep comparison
    8. Save results
    
    Args:
        job_id: Unique job identifier
        file_path: Path to uploaded file
        file_type: File extension (pdf, docx, txt, tex)
    """
    try:
        logger.info(f"Starting job {job_id}")
        
        # Update status to processing
        # TODO: update_job_status(job_id, {"status": "processing", "progress": 0})
        
        # Initialize pipeline
        pipeline = PlagiarismPipeline()
        
        # Check document against corpus
        result = pipeline.check_document(file_path, file_type, top_k=10)
        
        logger.info(f"Job {job_id} completed successfully")
        
        # Update status to done
        # TODO: save_check_result(job_id, result)
        # TODO: update_job_status(job_id, {"status": "done", "progress": 100})
        
        return {"job_id": job_id, "status": "done", "result": result}
        
    except FileNotFoundError as e:
        # Permanent error - file doesn't exist
        logger.error(f"Job {job_id} failed: File not found")
        # TODO: update_job_status(job_id, {
        #     "status": "failed",
        #     "error": "File not found",
        #     "can_retry": False
        # })
        raise PermanentError(str(e))
        
    except TimeoutError as e:
        # Transient error - might work on retry
        logger.warning(f"Job {job_id} timeout, retrying...")
        retry_delay = RETRY_DELAYS[min(self.request.retries, len(RETRY_DELAYS) - 1)]
        
        # TODO: update_job_status(job_id, {
        #     "status": "retrying",
        #     "retry_count": self.request.retries + 1,
        #     "next_retry_at": (datetime.now() + timedelta(seconds=retry_delay)).isoformat()
        # })
        
        raise self.retry(exc=e, countdown=retry_delay)
        
    except Exception as e:
        # Unknown error - retry once
        logger.error(f"Job {job_id} error: {str(e)}")
        
        if self.request.retries < 1:
            raise self.retry(exc=e, countdown=60)
        else:
            # TODO: update_job_status(job_id, {
            #     "status": "failed",
            #     "error": str(e),
            #     "can_retry": True
            # })
            raise


@app.task
def cleanup_old_jobs():
    """
    Periodic task to cleanup old jobs
    
    - Deletes jobs older than 30 days
    - Removes temp files
    """
    logger.info("Running cleanup task")
    # TODO: Implement cleanup logic
    pass


@app.task
def reset_daily_quotas():
    """
    Periodic task to reset daily quotas
    
    - Runs at midnight
    - Resets daily_checks and daily_uploads for all users
    """
    logger.info("Resetting daily quotas")
    # TODO: Implement quota reset
    pass
