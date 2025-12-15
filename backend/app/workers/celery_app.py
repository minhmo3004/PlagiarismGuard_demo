"""
Celery application configuration
"""
from celery import Celery
from app.config import settings

# Create Celery app
app = Celery(
    'plagiarism',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,  # One task at a time
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
)

# Auto-discover tasks
app.autodiscover_tasks(['app.workers'])
