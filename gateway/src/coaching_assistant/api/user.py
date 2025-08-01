"""
User management routes for the Coaching Transcript Tool Backend API.
Cloudflare Workers 版本，為未來的認證和訂閱功能準備。
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
async def user_root():
    """用戶 API 根端點"""
    return {"message": "User Management API v2.2 - CF Workers"}

@router.get("/profile")
async def get_user_profile():
    """
    獲取用戶資料 (暫時實作，未來整合真實認證)
    """
    # TODO: 實作真實的用戶認證和授權
    # TODO: 整合 CF KV 儲存用戶資料
    return {
        "user_id": "demo-user",
        "email": "demo@example.com", 
        "name": "Demo User",
        "subscription_tier": "free",
        "usage_count": 0,
        "usage_limit": 10
    }

@router.get("/usage")
async def get_user_usage():
    """
    獲取用戶使用情況統計
    """
    # TODO: 實作真實的使用量追蹤
    # TODO: 整合 CF Analytics 和 KV 儲存
    return {
        "current_month": {
            "processed_files": 0,
            "total_size_mb": 0.0,
            "remaining_quota": 10
        },
        "total": {
            "processed_files": 0,
            "total_size_mb": 0.0
        }
    }

@router.post("/feedback")
async def submit_feedback(feedback_data: Dict[str, Any]):
    """
    提交用戶反饋
    """
    logger.info(f"Received user feedback: {feedback_data}")
    # TODO: 實作反饋儲存機制，可能使用 CF R2 或外部服務
    return {"message": "Feedback received successfully"}
