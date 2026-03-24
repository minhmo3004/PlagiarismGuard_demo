"""
Celery tasks cho xử lý nền (background processing)
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

# Cấu hình retry
RETRY_DELAYS = [60, 300, 900]  # 1 phút, 5 phút, 15 phút
MAX_RETRIES = 3


class TransientError(Exception):
    """Lỗi tạm thời - nên thử lại (retry)"""
    pass


class PermanentError(Exception):
    """Lỗi vĩnh viễn - không nên thử lại"""
    pass


@app.task(bind=True, max_retries=MAX_RETRIES)
def process_document(self: Task, job_id: str, doc_id: str, file_type: str):
    """
    Xử lý tài liệu để kiểm tra đạo văn (background task)
    
    Các bước thực hiện:
    1. Kiểm tra tính hợp lệ của file
    2. Trích xuất văn bản
    3. Tiền xử lý (NLP tiếng Việt)
    4. Tạo shingles
    5. Tạo chữ ký MinHash
    6. Truy vấn LSH
    7. So sánh sâu (nếu cần)
    8. Lưu kết quả vào database
    
    Args:
        job_id: Mã công việc duy nhất
        doc_id: ID của tài liệu trong database
        file_type: Đuôi file (pdf, docx, txt, tex)
    """
    try:
        logger.info(f"Bắt đầu xử lý job {job_id} (doc={doc_id})")

        # Tạo session database
        db = SessionLocal()

        # Load thông tin tài liệu
        doc = None
        try:
            from app.db import models
            doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
            if not doc:
                raise FileNotFoundError("Không tìm thấy bản ghi tài liệu")

            # Tải file từ MinIO về file tạm
            storage = S3Storage()
            # s3_path thường có dạng "bucket/object"
            object_name = doc.s3_path.split('/', 1)[1] if '/' in doc.s3_path else doc.s3_path
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(doc.original_filename or '')[1] or '')
            tmp.close()
            storage.download_to_path(object_name, tmp.name)

            # Trích xuất văn bản tùy theo loại file
            if file_type in ('.pdf', 'pdf'):
                text, method = extract_text_with_fallback(tmp.name)
            elif file_type in ('.docx', 'docx'):
                text = extract_docx(tmp.name)
                method = 'python-docx'
            else:
                with open(tmp.name, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                method = 'direct'

            # Tiền xử lý văn bản tiếng Việt
            from app.services.preprocessing.vietnamese_nlp import preprocess_vietnamese
            tokens = preprocess_vietnamese(text)

            # Tạo shingles và MinHash signature
            shingles = create_shingles(tokens, k=7)
            if not shingles:
                raise ValueError("Không tạo được shingles")

            minhash = create_minhash_signature(shingles)

            # Lưu chữ ký vào Redis LSH
            similarity = SimilarityService()
            similarity.index_signature(str(doc.id), minhash)

            # Truy vấn LSH để tìm các tài liệu candidate
            candidates = similarity.query(minhash, top_k=10)

            # Cập nhật thông tin trích xuất cho Document
            word_count = len(tokens)
            page_count = None
            DocumentService.update_extracted_text(db, doc.id, text, word_count, page_count, method)

            # Lưu kết quả kiểm tra
            overall_similarity = max([score for (_, score) in candidates], default=0.0)
            result_count = len(candidates)

            # Cập nhật bản ghi CheckResult
            result = db.query(models.CheckResult).filter(models.CheckResult.id == job_id).first()
            if result:
                result.overall_similarity = overall_similarity
                result.match_count = result_count
                result.status = 'done'
                result.completed_at = datetime.now()
                db.add(result)
                db.commit()

            # TODO: Lưu chi tiết match_details (các đoạn trùng khớp)

            # Dọn dẹp file tạm
            try:
                os.unlink(tmp.name)
            except Exception:
                pass

            logger.info(f"Job {job_id} hoàn thành thành công")

            return {"job_id": job_id, "status": "done", "candidates": candidates}
        finally:
            db.close()
        
    except FileNotFoundError as e:
        # Lỗi vĩnh viễn - không nên retry
        logger.error(f"Job {job_id} thất bại: Không tìm thấy file")
        # TODO: Cập nhật trạng thái failed, can_retry=False
        raise PermanentError(str(e))
        
    except TimeoutError as e:
        # Lỗi tạm thời - có thể retry
        logger.warning(f"Job {job_id} timeout, đang thử lại...")
        retry_delay = RETRY_DELAYS[min(self.request.retries, len(RETRY_DELAYS) - 1)]
        
        # TODO: Cập nhật trạng thái retrying
        raise self.retry(exc=e, countdown=retry_delay)
        
    except Exception as e:
        # Lỗi không xác định - retry tối đa 1 lần
        logger.error(f"Job {job_id} gặp lỗi: {str(e)}")
        
        if self.request.retries < 1:
            raise self.retry(exc=e, countdown=60)
        else:
            # TODO: Cập nhật trạng thái failed
            raise


@app.task
def cleanup_old_jobs():
    """
    Task định kỳ dọn dẹp các job cũ
    
    - Xóa các job cũ hơn 30 ngày
    - Xóa file tạm không còn sử dụng
    """
    logger.info("Đang chạy task dọn dẹp job cũ")
    # TODO: Triển khai logic dọn dẹp
    pass


@app.task
def reset_daily_quotas():
    """
    Task định kỳ reset hạn mức sử dụng hàng ngày
    
    - Chạy vào lúc nửa đêm
    - Reset daily_checks và daily_uploads cho tất cả người dùng
    """
    logger.info("Đang reset hạn mức sử dụng hàng ngày")
    # TODO: Triển khai logic reset quota
    pass