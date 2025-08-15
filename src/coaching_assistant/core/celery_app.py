"""Celery application configuration."""

from celery import Celery
from celery import signals
from .config import settings
import logging
import os


# 設置統一的日誌配置
def setup_celery_worker_logging():
    """為 Celery worker 設置統一的日誌配置"""
    # 判斷當前是否為 debug 模式
    log_level = os.getenv("CELERY_LOG_LEVEL", "INFO")

    # 使用絕對路徑確保日誌文件位置正確
    import pathlib

    project_root = pathlib.Path(__file__).parent.parent.parent.parent.parent.parent
    log_file = (
        project_root
        / "logs"
        / ("celery-debug.log" if log_level == "DEBUG" else "celery.log")
    )

    # 使用獨立的日誌設置，不影響其他logger
    from ..middleware.logging import setup_logging

    setup_logging(
        level=log_level,
        log_file=str(log_file),
        enable_file_logging=True,
        logger_name="celery",
    )


logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery("coaching_assistant")

# Configure Celery
celery_app.conf.update(
    # Broker settings
    broker_url=settings.REDIS_URL
    or settings.CELERY_BROKER_URL
    or "redis://localhost:6379/0",
    result_backend=settings.REDIS_URL
    or settings.CELERY_RESULT_BACKEND
    or "redis://localhost:6379/0",
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Logging settings - separate Celery logs from API logs
    worker_hijack_root_logger=False,
    worker_log_color=False,
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


# 設置 worker 啟動時的回調函數
@signals.worker_init.connect
def setup_worker_logging(sender=None, **kwargs):
    """當 worker 啟動時設置日誌配置"""
    setup_celery_worker_logging()
    logger.info("Celery worker logging configured successfully")


logger.info("Celery app configured successfully")
