"""
Plan limits validation API endpoints.
Handles usage validation and limit checking for different plan tiers.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from coaching_assistant.core.database import get_db
from .auth import get_current_user_dependency
from coaching_assistant.models.user import User
from coaching_assistant.services.usage_tracker import UsageTracker
from coaching_assistant.services.plan_limits import get_global_plan_limits, PlanName
from coaching_assistant.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["plan-limits"])


class ValidateActionRequest(BaseModel):
    """Request model for action validation."""

    action: str = Field(
        ...,
        description="Action to validate: create_session, transcribe, check_minutes, upload_file, export_transcript",
    )
    params: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Optional parameters for validation"
    )


class LimitInfo(BaseModel):
    """Information about current usage and limits."""

    type: str = Field(
        ...,
        description="Type of limit: sessions, transcriptions, minutes, file_size, exports",
    )
    current: int = Field(..., description="Current usage count")
    limit: int = Field(..., description="Plan limit (-1 for unlimited)")
    reset_date: str = Field(
        ..., description="ISO format date when limits reset"
    )


class UpgradeSuggestion(BaseModel):
    """Upgrade suggestion when limit is reached."""

    plan_id: str = Field(..., description="Suggested plan ID")
    display_name: str = Field(..., description="Display name of the plan")
    benefits: list[str] = Field(..., description="Key benefits of upgrading")


class ValidateActionResponse(BaseModel):
    """Response model for action validation."""

    allowed: bool = Field(..., description="Whether the action is allowed")
    message: Optional[str] = Field(None, description="Human-readable message")
    limit_info: Optional[LimitInfo] = Field(
        None, description="Current usage and limit information"
    )
    upgrade_suggestion: Optional[UpgradeSuggestion] = Field(
        None, description="Upgrade suggestion if limit reached"
    )


@router.post("/validate-action", response_model=ValidateActionResponse)
async def validate_action(
    request: ValidateActionRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
) -> ValidateActionResponse:
    """
    Validate if a user can perform a specific action based on their plan limits.

    Actions:
    - create_session: Check if user can create a new coaching session
    - transcribe: Check if user can create a new transcription
    - check_minutes: Check if user has minutes available (params: duration_min)
    - upload_file: Check file size limit (params: file_size_mb)
    - export_transcript: Check export limit
    """
    try:
        # Initialize usage tracker
        tracker = UsageTracker(db)

        # Get user's current plan
        if current_user.plan:
            # Handle UserPlan enum conversion to PlanName
            plan_value = (
                current_user.plan.value
                if hasattr(current_user.plan, "value")
                else str(current_user.plan)
            )
            user_plan = PlanName(plan_value)
        else:
            user_plan = PlanName.FREE
        plan_limits_service = get_global_plan_limits()
        plan_limits = plan_limits_service.get_plan_limit(user_plan)

        # Get reset date (first day of next month)
        now = datetime.utcnow()
        if now.month == 12:
            reset_date = datetime(now.year + 1, 1, 1)
        else:
            reset_date = datetime(now.year, now.month + 1, 1)
        reset_date_str = reset_date.isoformat() + "Z"

        # Validate based on action type - Phase 2: Only minutes-based limits
        if request.action == "create_session":
            # Sessions are now unlimited - always allowed
            current_usage = current_user.session_count or 0
            limit = -1  # Unlimited
            limit_type = "sessions"
            allowed = True
            message = None

        elif request.action == "transcribe":
            # Transcriptions are now unlimited - always allowed
            current_usage = current_user.transcription_count or 0
            limit = -1  # Unlimited
            limit_type = "transcriptions"
            allowed = True
            message = None

        elif request.action == "check_minutes":
            current_usage = current_user.usage_minutes or 0
            limit = plan_limits.max_minutes
            limit_type = "minutes"

            # Check if adding requested minutes would exceed limit
            requested_minutes = (
                request.params.get("duration_min", 0) if request.params else 0
            )
            projected_usage = current_usage + requested_minutes

            allowed = limit == -1 or projected_usage <= limit

            if not allowed:
                message = "You have reached your monthly audio minutes limit"
            else:
                message = None

        elif request.action == "upload_file":
            file_size_mb = (
                request.params.get("file_size_mb", 0) if request.params else 0
            )
            limit = plan_limits.max_file_size_mb
            limit_type = "file_size"
            current_usage = (
                file_size_mb  # For file size, current is the requested size
            )

            allowed = file_size_mb <= limit

            if not allowed:
                message = f"File size exceeds your plan limit of {limit}MB"
            else:
                message = None

        elif request.action == "export_transcript":
            # For exports, we'll track it separately if needed
            # For now, use session count as a proxy
            current_usage = current_user.session_count or 0
            limit = (
                plan_limits.max_exports_per_month
                if hasattr(plan_limits, "max_exports_per_month")
                else 50
            )
            limit_type = "exports"

            allowed = limit == -1 or current_usage < limit

            if not allowed:
                message = "You have reached your monthly export limit"
            else:
                message = None

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {request.action}",
            )

        # Build response
        response = ValidateActionResponse(
            allowed=allowed,
            message=message,
            limit_info=LimitInfo(
                type=limit_type,
                current=int(current_usage),
                limit=int(limit),
                reset_date=reset_date_str,
            ),
        )

        # Add upgrade suggestion if limit reached and not on highest plan
        if not allowed and user_plan != PlanName.COACHING_SCHOOL:
            if user_plan == PlanName.FREE:
                response.upgrade_suggestion = UpgradeSuggestion(
                    plan_id="STUDENT",
                    display_name="學習方案",
                    benefits=[
                        "每月 500 分鐘音檔額度",
                        "最大檔案 100MB",
                        "所有匯出格式",
                        "6 個月資料保存",
                    ],
                )
            elif user_plan == PlanName.STUDENT:
                response.upgrade_suggestion = UpgradeSuggestion(
                    plan_id="PRO",
                    display_name="專業方案",
                    benefits=[
                        "每月 3000 分鐘音檔額度",
                        "最大檔案 200MB",
                        "優先 Email 支援",
                        "進階分析報告",
                    ],
                )
            elif user_plan == PlanName.PRO:
                response.upgrade_suggestion = UpgradeSuggestion(
                    plan_id="COACHING_SCHOOL",
                    display_name="認證學校方案",
                    benefits=[
                        "無限制音檔額度",
                        "專屬支援",
                        "自訂整合功能",
                        "團隊協作功能",
                    ],
                )

        logger.info(
            f"Validation for user {current_user.id}: action={request.action}, allowed={allowed}"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error validating action for user {current_user.id}: {str(e)}"
        )
        # Fail open - allow action on error
        return ValidateActionResponse(
            allowed=True,
            message="Validation temporarily unavailable, proceeding with action",
            limit_info=None,
            upgrade_suggestion=None,
        )


@router.get("/current-usage")
async def get_current_usage(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get current usage statistics for the authenticated user."""
    try:
        if current_user.plan:
            # Handle UserPlan enum conversion to PlanName
            plan_value = (
                current_user.plan.value
                if hasattr(current_user.plan, "value")
                else str(current_user.plan)
            )
            user_plan = PlanName(plan_value)
        else:
            user_plan = PlanName.FREE
        plan_limits_service = get_global_plan_limits()
        plan_limits = plan_limits_service.get_plan_limit(user_plan)

        # Calculate reset date
        now = datetime.utcnow()
        if now.month == 12:
            reset_date = datetime(now.year + 1, 1, 1)
        else:
            reset_date = datetime(now.year, now.month + 1, 1)

        return {
            "plan": user_plan.value,
            "usage": {
                # Phase 2: Only minutes-based limits, sessions/transcriptions unlimited
                "minutes": {
                    "current": current_user.usage_minutes or 0,
                    "limit": plan_limits.max_minutes,
                    "percentage": calculate_percentage(
                        current_user.usage_minutes or 0,
                        plan_limits.max_minutes,
                    ),
                },
                "file_size_mb": {"limit": plan_limits.max_file_size_mb},
            },
            "reset_date": reset_date.isoformat() + "Z",
            "days_until_reset": (reset_date - now).days,
        }

    except Exception as e:
        logger.error(
            f"Error getting usage for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage information",
        )


@router.post("/increment-usage")
async def increment_usage(
    metric: str,
    amount: int = 1,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Increment usage counter for a specific metric.
    This endpoint is typically called after a successful action.

    Metrics: session_count, transcription_count, usage_minutes
    """
    try:
        tracker = UsageTracker(db)

        # Validate metric
        valid_metrics = [
            "session_count",
            "transcription_count",
            "usage_minutes",
        ]
        if metric not in valid_metrics:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid metric: {metric}. Must be one of {valid_metrics}",
            )

        # Increment the usage
        new_value = tracker.increment_usage(current_user.id, metric, amount)

        logger.info(
            f"Incremented {metric} by {amount} for user {current_user.id}. New value: {new_value}"
        )

        return {
            "metric": metric,
            "amount_added": amount,
            "new_value": new_value,
            "success": True,
        }

    except Exception as e:
        logger.error(
            f"Error incrementing usage for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update usage",
        )


@router.post("/reset-monthly-usage")
async def reset_monthly_usage(
    admin_key: str, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Reset monthly usage counters for all users.
    This endpoint should be called by a scheduled job at the start of each month.
    Requires admin key for security.
    """
    # Verify admin key
    if admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin key"
        )

    try:
        tracker = UsageTracker(db)
        reset_count = tracker.reset_all_monthly_usage()

        logger.info(f"Reset monthly usage for {reset_count} users")

        return {
            "success": True,
            "users_reset": reset_count,
            "reset_time": datetime.utcnow().isoformat() + "Z",
        }

    except Exception as e:
        logger.error(f"Error resetting monthly usage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset usage",
        )


def calculate_percentage(current: int, limit: int) -> float:
    """Calculate usage percentage, handling unlimited (-1) cases."""
    if limit == -1:
        return 0.0  # Unlimited shows as 0%
    if limit == 0:
        return 100.0  # No limit means fully used
    return min(100.0, (current / limit) * 100)
