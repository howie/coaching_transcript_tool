"""
Health check routes for the Coaching Transcript Tool Backend API.
"""

import os
import time
from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    基本健康檢查端點。
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "coaching-transcript-tool-api",
        "version": "2.0.0",
    }


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    詳細的健康檢查端點，包含基本系統資訊。
    """
    try:
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "service": "coaching-transcript-tool-api",
            "version": "2.0.0",
            "system": {
                "platform": os.name,
                "python_version": os.sys.version.split()[0],
                "environment": os.getenv("ENVIRONMENT", "development"),
                "process_id": os.getpid(),
            },
        }
    except Exception as e:
        return {
            "status": "degraded",
            "timestamp": time.time(),
            "service": "coaching-transcript-tool-api",
            "version": "2.0.0",
            "error": str(e),
        }
