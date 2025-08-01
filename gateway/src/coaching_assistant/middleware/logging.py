"""
Logging configuration for the Coaching Transcript Tool Backend API.
Cloudflare Workers 優化版本。
"""
import logging
import sys
from typing import Dict, Any

def setup_logging(level: str = "INFO") -> None:
    """
    設定應用程式的日誌配置。
    CF Workers 環境優化。
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
    
    # CF Workers 特殊日誌設定
    logging.getLogger("cloudflare").setLevel(logging.INFO)
