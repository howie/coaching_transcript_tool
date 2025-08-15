"""
User management routes for the Coaching Transcript Tool Backend API.

用戶管理 API，提供用戶資料和偏好設定管理。
"""

import logging
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext

from ..core.database import get_db
from ..models.user import User, UserPlan
from ..api.auth import get_current_user_dependency

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()


class UserProfileResponse(BaseModel):
    id: UUID
    email: EmailStr
    name: str
    plan: UserPlan
    auth_provider: str
    google_connected: bool
    preferences: Dict[str, Any]

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None


class UpdatePreferencesRequest(BaseModel):
    language: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class SetPasswordRequest(BaseModel):
    new_password: str


@router.get("/")
async def user_root():
    """用戶 API 根端點"""
    return {"message": "User Management API v3.0"}


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(current_user: User = Depends(get_current_user_dependency)):
    """
    獲取當前用戶資料
    """
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        plan=current_user.plan,
        auth_provider=current_user.auth_provider,
        google_connected=current_user.google_connected,
        preferences=current_user.get_preferences(),
    )


@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """
    更新用戶資料
    """
    if profile_data.name is not None:
        current_user.name = profile_data.name

    db.commit()
    db.refresh(current_user)

    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        plan=current_user.plan,
        auth_provider=current_user.auth_provider,
        google_connected=current_user.google_connected,
        preferences=current_user.get_preferences(),
    )


@router.put("/preferences")
async def update_user_preferences(
    preferences_data: UpdatePreferencesRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """
    更新用戶偏好設定
    """
    # Build preferences dict from request
    prefs_update = {}
    if preferences_data.language is not None:
        if preferences_data.language not in ["zh", "en", "system"]:
            raise HTTPException(status_code=400, detail="Invalid language preference")
        prefs_update["language"] = preferences_data.language

    # Update preferences
    current_user.set_preferences(prefs_update)
    db.commit()

    return {
        "message": "Preferences updated successfully",
        "preferences": current_user.get_preferences(),
    }


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """
    更改密碼（僅適用於 email 登入用戶）
    """
    if current_user.auth_provider != "email":
        raise HTTPException(
            status_code=400, detail="Password change not available for SSO users"
        )

    if not current_user.hashed_password:
        raise HTTPException(
            status_code=400, detail="No password set. Use set-password endpoint."
        )

    # Verify current password
    if not pwd_context.verify(
        password_data.current_password, current_user.hashed_password
    ):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    # Set new password
    current_user.hashed_password = pwd_context.hash(password_data.new_password)
    db.commit()

    return {"message": "Password changed successfully"}


@router.post("/set-password")
async def set_password(
    password_data: SetPasswordRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """
    設定密碼（適用於 Google SSO 用戶首次設定密碼）
    """
    if current_user.hashed_password:
        raise HTTPException(
            status_code=400,
            detail="Password already set. Use change-password endpoint.",
        )

    # Set password for SSO user
    current_user.hashed_password = pwd_context.hash(password_data.new_password)
    db.commit()

    return {"message": "Password set successfully"}


@router.delete("/account")
async def delete_account(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """
    刪除用戶帳戶
    """
    db.delete(current_user)
    db.commit()

    return {"message": "Account deleted successfully"}


@router.get("/usage")
async def get_user_usage(current_user: User = Depends(get_current_user_dependency)):
    """
    獲取用戶使用情況統計
    """
    return {
        "current_month": {
            "processed_files": 0,
            "total_size_mb": 0.0,
            "remaining_quota": (
                60 - current_user.usage_minutes
                if current_user.plan == UserPlan.FREE
                else 600 - current_user.usage_minutes
            ),
        },
        "total": {
            "processed_files": 0,
            "total_size_mb": 0.0,
            "usage_minutes": current_user.usage_minutes,
        },
    }


@router.post("/feedback")
async def submit_feedback(
    feedback_data: Dict[str, Any],
    current_user: User = Depends(get_current_user_dependency),
):
    """
    提交用戶反饋
    """
    logger.info(f"Received user feedback from {current_user.email}: {feedback_data}")
    return {"message": "Feedback received successfully"}
