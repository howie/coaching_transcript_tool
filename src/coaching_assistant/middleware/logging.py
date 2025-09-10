"""
Logging configuration for the Coaching Transcript Tool Backend API.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    enable_file_logging: bool = True,
    logger_name: str = "",
) -> None:
    """
    設定應用程式的日誌配置。

    Args:
        level: 日誌級別 (DEBUG, INFO, WARNING, ERROR)
        log_file: 日誌文件路径 (如果为 None 则不输出到文件)
        enable_file_logging: 是否启用文件日志输出
    """
    # 創建 logs 目錄
    if enable_file_logging:
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

    # 配置日誌格式 (Celery 風格)
    formatter = CeleryStyleFormatter()

    # 如果指定了 logger 名稱，只配置特定的 logger，否則配置 root logger
    if logger_name:
        target_logger = logging.getLogger(logger_name)
        # 清除現有的 handlers
        for handler in target_logger.handlers[:]:
            target_logger.removeHandler(handler)
    else:
        # 清除現有的 handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        target_logger = root_logger

    handlers = []

    # 控制台輸出 (Celery 風格帶顏色)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CeleryStyleColoredFormatter())
    handlers.append(console_handler)

    # 文件輸出 (如果指定)
    if enable_file_logging and log_file:
        # 使用 RotatingFileHandler 防止日誌文件過大
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=5,  # 保留 5 個備份
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # 設定日誌配置
    if logger_name:
        # 為特定 logger 設定
        target_logger.setLevel(getattr(logging, level.upper()))
        for handler in handlers:
            target_logger.addHandler(handler)
        target_logger.propagate = False  # 不向上級 logger 傳播
    else:
        # 設定基本配置
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            handlers=handlers,
            force=True,  # 強制重新配置
        )

    # 設定第三方套件的日誌級別
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.WARNING
    )  # 減少 SQL 日誌


class CeleryStyleFormatter(logging.Formatter):
    """Celery 風格的日誌格式化器（無顏色，用於檔案輸出）"""

    def __init__(self):
        super().__init__()

    def format(self, record):
        # 格式化時間戳，包含毫秒
        import datetime

        created_time = datetime.datetime.fromtimestamp(record.created)
        timestamp = created_time.strftime("%Y-%m-%d %H:%M:%S,%f")[
            :-3
        ]  # 去掉後3位微秒，保留毫秒

        # Celery 風格格式: [YYYY-MM-DD HH:MM:SS,mmm: LEVEL/ProcessName] message
        process_name = getattr(record, "processName", "MainProcess")
        formatted = f"[{timestamp}: {record.levelname}/{process_name}] {record.getMessage()}"

        # 如果有異常，加入異常資訊
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            formatted += "\n" + record.exc_text

        return formatted


class CeleryStyleColoredFormatter(CeleryStyleFormatter):
    """Celery 風格的帶顏色日誌格式化器（用於控制台輸出）"""

    # Celery 使用的顏色方案
    COLORS = {
        "DEBUG": "\033[37m",  # 白色
        "INFO": "\033[0m",  # 預設顏色
        "WARNING": "\033[33m",  # 黃色
        "ERROR": "\033[31m",  # 紅色
        "CRITICAL": "\033[35m",  # 紫色
    }
    RESET = "\033[0m"

    def format(self, record):
        formatted = super().format(record)

        # 如果輸出是 TTY，添加顏色
        if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
            color = self.COLORS.get(record.levelname, "")
            if color:
                # 只給 levelname 部分加顏色
                import re

                formatted = re.sub(
                    rf"\[([^:]+): ({record.levelname})/([^\]]+)\]",
                    rf"[\1: {color}\2{self.RESET}/\3]",
                    formatted,
                )

        return formatted


def setup_celery_logging(log_file: str = "logs/celery.log") -> None:
    """為 Celery worker 設置專用的日誌配置"""
    setup_logging(level="INFO", log_file=log_file, enable_file_logging=True)


def setup_api_logging(log_file: str = "logs/api.log") -> None:
    """為 FastAPI 設置專用的日誌配置"""
    setup_logging(level="INFO", log_file=log_file, enable_file_logging=True)
