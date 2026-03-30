"""
Celery tasks for background processing
"""
from celery import Task
from celery.exceptions import MaxRetriesExceededError
from app.workers.celery_app import app
from app.db.database import SessionLocal
from app.services.document_service import DocumentService
from app.services.plagiarism_checker import PlagiarismChecker
from app.api.deps import get_minio_storage
import tempfile
import os
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


from redis import Redis
import uuid
import json
from app.core.config import settings

@app.task(bind=True, max_retries=MAX_RETRIES)
def process_document(self: Task, job_id: str, doc_id: str, file_type: str):
    """
    Process document for plagiarism check (Production Implementation)
    """
    db = SessionLocal()
    try:
        logger.info(f"🚀 Starting background job {job_id} (doc={doc_id})")

        # 1. Load records
        from app.db import models
        doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
        result = db.query(models.CheckResult).filter(models.CheckResult.id == job_id).first()
        
        if not doc or not result:
            logger.error(f"❌ Document {doc_id} or Result {job_id} not found")
            return {"job_id": job_id, "status": "failed", "error": "Records not found"}

        result.status = 'processing'
        db.commit()

        # 2. Setup Services
        redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        checker = PlagiarismChecker(redis_client=redis_client)
        storage = get_minio_storage()

        # 3. Download and Extract
        try:
            object_name = result.file_path # Using relative path stored in upload
            tmp_suffix = os.path.splitext(doc.original_filename or '')[1] or file_type
            with tempfile.NamedTemporaryFile(delete=False, suffix=tmp_suffix) as tmp:
                tmp_path = tmp.name
            
            storage.download_file(object_name) # MinIOStorage logic - though internal extraction is preferred
            # Using checker's internal extraction logic
            text = checker._extract_text(tmp_path, doc.original_filename)
        except Exception as e:
            logger.error(f"❌ Extraction error: {e}")
            result.status = 'failed'
            result.error_message = f"Lỗi trích xuất văn bản: {str(e)}"
            db.commit()
            return {"job_id": job_id, "status": "failed", "error": str(e)}

        # 4. Perform Plagiarism Check
        start_time = datetime.now()
        check_result = checker.check_against_corpus(tmp_path, doc.original_filename)
        end_time = datetime.now()
        
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # 5. Update Document Extracted Text
        DocumentService.update_extracted_text(
            db, doc.id, text, check_result.word_count, None, 'celery-worker'
        )

        # 6. Save Overall Result
        result.overall_similarity = check_result.overall_similarity
        result.plagiarism_level = check_result.plagiarism_level
        result.match_count = len(check_result.matches)
        result.word_count = check_result.word_count
        result.processing_time_ms = duration_ms
        result.status = 'done'
        result.completed_at = datetime.now()

        # 7. Save Match Details
        # Clear any existing (shouldn't be any for new job)
        db.query(models.MatchDetail).filter(models.MatchDetail.result_id == result.id).delete()
        
        for m in check_result.matches:
            # Re-fetch source doc by UUID if possible (checker uses doc_id prefix)
            # Find complete doc in DB
            source_doc = db.query(models.Document).filter(
                models.Document.is_corpus == 1
            ).filter(
                db.cast(models.Document.id, db.String).like(f"{m.doc_id}%")
            ).first()

            detail = models.MatchDetail(
                result_id=result.id,
                source_doc_id=source_doc.id if source_doc else None,
                similarity_score=m.similarity,
                source_title=m.title or (source_doc.title if source_doc else "Unknown"),
                source_author=m.author or (source_doc.author if source_doc else "Unknown"),
                source_university=m.university or (source_doc.university if source_doc else "Unknown"),
                source_year=m.year or (source_doc.year if source_doc else None),
                matched_segments=json.dumps([
                    {
                        "query_text": seg.query_text,
                        "query_start": seg.query_start,
                        "query_end": seg.query_end,
                        "source_text": seg.source_text,
                        "source_start": seg.source_start,
                        "source_end": seg.source_end
                    } for seg in (m.matched_segments or [])
                ])
            )
            db.add(detail)

        db.commit()
        logger.info(f"✅ Job {job_id} done. matches={len(check_result.matches)}")

        # Cleanup
        try:
            os.unlink(tmp_path)
        except:
            pass

        return {"job_id": job_id, "status": "done", "matches": len(check_result.matches)}

    except Exception as e:
        logger.error(f"❌ Unhandled Job Error: {e}", exc_info=True)
        db.rollback()
        # Reset status if possible
        try:
            res = db.query(models.CheckResult).filter(models.CheckResult.id == job_id).first()
            if res:
                res.status = 'failed'
                res.error_message = str(e)
                db.commit()
        except:
            pass
        
        if self.request.retries < MAX_RETRIES:
            raise self.retry(exc=e, countdown=60)
        raise PermanentError(str(e))
    finally:
        db.close()


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
