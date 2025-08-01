"""
Logging configuration for the Coaching Transcript Tool Backend API.
"""
import logging
import sys
from typing import Dict, Any

def setup_logging(level: str = "INFO") -> None:
    """
    設定應用程式的日誌配置。
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 設定第三方套件的日誌級別
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
