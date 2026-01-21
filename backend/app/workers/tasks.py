"""
Celery tasks for background processing
"""
from celery import Task
from celery.exceptions import MaxRetriesExceededError
from app.workers.celery_app import app
from app.services.algorithm.pipeline import PlagiarismPipeline
from app.db.database import SessionLocal
from app.services.storage import S3Storage
from app.services.document_service import DocumentService
from app.services.similarity_service import SimilarityService
from app.services.algorithm.shingling import create_shingles
from app.services.algorithm.minhash import create_minhash_signature
from app.services.preprocessing.pdf_extractor import extract_text_with_fallback
from app.services.preprocessing.pipeline import extract_docx
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


@app.task(bind=True, max_retries=MAX_RETRIES)
def process_document(self: Task, job_id: str, doc_id: str, file_type: str):
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
        logger.info(f"Starting job {job_id} (doc={doc_id})")

        # DB session
        db = SessionLocal()

        # Load document record
        doc = None
        try:
            from app.db import models
            doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
            if not doc:
                raise FileNotFoundError("Document record not found")

            # Download file from MinIO to temp file
            storage = S3Storage()
            # s3_path stored as "bucket/object"
            object_name = doc.s3_path.split('/', 1)[1] if '/' in doc.s3_path else doc.s3_path
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(doc.original_filename or '')[1] or '')
            tmp.close()
            storage.download_to_path(object_name, tmp.name)

            # Extract text
            if file_type == '.pdf' or file_type == 'pdf':
                text, method = extract_text_with_fallback(tmp.name)
            elif file_type == '.docx' or file_type == 'docx':
                text = extract_docx(tmp.name)
                method = 'python-docx'
            else:
                with open(tmp.name, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                method = 'direct'

            # Preprocess -> tokens
            from app.services.preprocessing.vietnamese_nlp import preprocess_vietnamese
            tokens = preprocess_vietnamese(text)

            # Create shingles and MinHash
            shingles = create_shingles(tokens, k=7)
            if not shingles:
                raise ValueError("No shingles generated")

            minhash = create_minhash_signature(shingles)

            # Index signature to Redis LSH
            similarity = SimilarityService()
            similarity.index_signature(str(doc.id), minhash)

            # Query LSH for candidates
            candidates = similarity.query(minhash, top_k=10)

            # Update document with extracted text and stats
            word_count = len(tokens)
            page_count = None
            DocumentService.update_extracted_text(db, doc.id, text, word_count, page_count, method)

            # Save check result
            overall_similarity = max([score for (_, score) in candidates], default=0.0)
            result_count = len(candidates)

            # Update CheckResult record
            result = db.query(models.CheckResult).filter(models.CheckResult.id == job_id).first()
            if result:
                result.overall_similarity = overall_similarity
                result.match_count = result_count
                result.status = 'done'
                result.completed_at = datetime.now()
                db.add(result)
                db.commit()

            # Optionally store match_details
            # TODO: expand to store detailed segments

            # Cleanup temp file
            try:
                os.unlink(tmp.name)
            except Exception:
                pass

            logger.info(f"Job {job_id} completed successfully")

            return {"job_id": job_id, "status": "done", "candidates": candidates}
        finally:
            db.close()
        
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
