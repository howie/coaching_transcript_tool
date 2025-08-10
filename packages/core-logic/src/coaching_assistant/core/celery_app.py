"""Celery application configuration."""

from celery import Celery
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery("coaching_assistant")

# Configure Celery
celery_app.conf.update(
    # Broker settings
    broker_url=settings.REDIS_URL or settings.CELERY_BROKER_URL or "redis://localhost:6379/0",
    result_backend=settings.REDIS_URL or settings.CELERY_RESULT_BACKEND or "redis://localhost:6379/0",
    
    # Task settings  
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_routes={
        "coaching_assistant.tasks.transcribe_audio": {"queue": "transcription"},
    },
    
    # Worker settings
    worker_concurrency=4,
    worker_prefetch_multiplier=1,
    
    # Task time limits
    task_time_limit=7200,  # 2 hours hard limit
    task_soft_time_limit=6900,  # 1h 55m soft limit
    
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Result settings
    result_expires=3600,  # 1 hour
    
    # Error handling
    task_ignore_result=False,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["coaching_assistant.tasks"])

logger.info("Celery app configured successfully")