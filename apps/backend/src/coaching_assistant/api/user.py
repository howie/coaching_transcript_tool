"""
User management routes for the Coaching Transcript Tool Backend API.

用戶管理 API，為未來的認證和訂閱功能準備。
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
async def user_root():
    """用戶 API 根端點"""
    return {"message": "User Management API v2.0"}

@router.get("/profile")
async def get_user_profile():
    """
    獲取用戶資料 (暫時實作，未來整合真實認證)
    """
    # TODO: 實作真實的用戶認證和授權
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
    # TODO: 實作反饋儲存機制
    return {"message": "Feedback received successfully"}
