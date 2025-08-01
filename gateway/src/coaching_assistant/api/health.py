"""
Health check routes for the Coaching Transcript Tool Backend API.
Cloudflare Workers 版本。
"""
from fastapi import APIRouter
from typing import Dict, Any
import time
import os

router = APIRouter()

@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    基本健康檢查端點。
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "coaching-transcript-tool-cf-workers",
        "version": "2.2.0"
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
            "service": "coaching-transcript-tool-cf-workers",
            "version": "2.2.0",
            "system": {
                "platform": "cloudflare-workers",
                "python_version": os.sys.version.split()[0] if hasattr(os, 'sys') else "unknown",
                "environment": os.getenv("ENVIRONMENT", "production"),
                "worker_id": os.getenv("CF_RAY", "unknown")
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "timestamp": time.time(),
            "service": "coaching-transcript-tool-cf-workers",
            "version": "2.2.0",
            "error": str(e)
        }
