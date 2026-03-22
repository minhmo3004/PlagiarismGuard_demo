"""
Cấu hình ứng dụng Celery (xử lý tác vụ nền bất đồng bộ)
"""
from celery import Celery
from app.config import settings

# Khởi tạo ứng dụng Celery
app = Celery(
    'plagiarism',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Cấu hình Celery
app.conf.update(
    task_serializer='json',              # Định dạng serialize cho task
    accept_content=['json'],             # Chỉ chấp nhận dữ liệu JSON
    result_serializer='json',            # Định dạng serialize kết quả
    timezone='UTC',                      # Múi giờ hệ thống
    enable_utc=True,                     # Bật chế độ UTC
    task_track_started=True,             # Theo dõi trạng thái task (started)
    
    task_time_limit=3600,                # Thời gian tối đa cho mỗi task (giây) - 1 giờ
    task_soft_time_limit=3300,           # Giới hạn mềm (giây) - 55 phút
    
    worker_prefetch_multiplier=1,        # Mỗi worker xử lý 1 task tại một thời điểm
    worker_max_tasks_per_child=100,      # Restart worker sau 100 task (tránh memory leak)
)

# Tự động phát hiện các task trong module workers
app.autodiscover_tasks(['app.workers'])