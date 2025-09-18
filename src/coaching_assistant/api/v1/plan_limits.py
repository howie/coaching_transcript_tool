"""
Plan limits validation API endpoints.
Handles usage validation and limit checking for different plan tiers.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .auth import get_current_user_dependency
from .dependencies import get_plan_validation_use_case, get_plan_retrieval_use_case, get_usage_log_use_case, get_user_usage_use_case
from coaching_assistant.models.user import User
from coaching_assistant.core.services.plan_management_use_case import PlanValidationUseCase, PlanRetrievalUseCase
from coaching_assistant.core.services.usage_tracking_use_case import CreateUsageLogUseCase, GetUserUsageUseCase
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
    plan_validation_use_case: PlanValidationUseCase = Depends(get_plan_validation_use_case),
) -> ValidateActionResponse:
    """
    Validate if a user can perform a specific action based on their plan limits using Clean Architecture.

    Actions:
    - create_session: Check if user can create a new coaching session
    - transcribe: Check if user can create a new transcription
    - check_minutes: Check if user has minutes available (params: duration_min)
    - upload_file: Check file size limit (params: file_size_mb)
    - export_transcript: Check export limit
    """
    try:
        # Get reset date (first day of next month)
        now = datetime.utcnow()
        if now.month == 12:
            reset_date = datetime(now.year + 1, 1, 1)
        else:
            reset_date = datetime(now.year, now.month + 1, 1)
        reset_date_str = reset_date.isoformat() + "Z"

        # Handle different validation types using the use case
        if request.action == "upload_file":
            file_size_mb = (
                request.params.get("file_size_mb", 0) if request.params else 0
            )
            # Use file size validation from the use case
            file_validation = plan_validation_use_case.validate_file_size(current_user.id, file_size_mb)

            response = ValidateActionResponse(
                allowed=file_validation["valid"],
                message=file_validation["message"],
                limit_info=LimitInfo(
                    type="file_size",
                    current=int(file_validation.get("actual", file_size_mb)),
                    limit=int(file_validation.get("limit", 60)),
                    reset_date=reset_date_str,
                ) if not file_validation["valid"] else LimitInfo(
                    type="file_size",
                    current=int(file_size_mb),
                    limit=int(file_validation.get("limit", 60)),
                    reset_date=reset_date_str,
                ),
            )
        else:
            # For other actions, use general usage validation
            usage_validation = plan_validation_use_case.validate_user_limits(current_user.id)

            # Determine current usage and limits based on action
            if request.action in ["create_session", "transcribe"]:
                # These are now unlimited in the new plan system
                response = ValidateActionResponse(
                    allowed=True,
                    message=None,
                    limit_info=LimitInfo(
                        type=request.action.replace("create_", "").replace("transcribe", "transcription"),
                        current=getattr(current_user, "session_count" if request.action == "create_session" else "transcription_count", 0) or 0,
                        limit=-1,  # Unlimited
                        reset_date=reset_date_str,
                    ),
                )
            elif request.action == "check_minutes":
                # Minutes validation based on requested duration
                requested_minutes = (
                    request.params.get("duration_min", 0) if request.params else 0
                )
                current_minutes = getattr(current_user, "usage_minutes", 0) or 0

                # Check if any violations would occur with the additional minutes
                allowed = usage_validation["valid"]
                message = "Action permitted"

                if usage_validation["violations"]:
                    for violation in usage_validation["violations"]:
                        if violation["type"] == "total_minutes":
                            if current_minutes + requested_minutes > violation["limit"]:
                                allowed = False
                                message = violation["message"]
                            break

                response = ValidateActionResponse(
                    allowed=allowed,
                    message=message if not allowed else None,
                    limit_info=LimitInfo(
                        type="minutes",
                        current=current_minutes,
                        limit=usage_validation["limits"].get("maxMinutes", -1),
                        reset_date=reset_date_str,
                    ),
                )
            else:
                # Default case for export_transcript or other actions
                response = ValidateActionResponse(
                    allowed=usage_validation["valid"],
                    message=usage_validation.get("message", "Action permitted") if not usage_validation["valid"] else None,
                    limit_info=LimitInfo(
                        type=request.action.replace("export_", ""),
                        current=0,  # Would need specific tracking
                        limit=50,   # Default export limit
                        reset_date=reset_date_str,
                    ),
                )

        # Add upgrade suggestions based on current plan
        current_plan_value = getattr(current_user.plan, 'value', current_user.plan) if hasattr(current_user.plan, 'value') else current_user.plan

        if not response.allowed and current_plan_value != "ENTERPRISE":
            if current_plan_value == "FREE":
                response.upgrade_suggestion = UpgradeSuggestion(
                    plan_id="PRO",
                    display_name="專業方案",
                    benefits=[
                        "更多音檔處理額度",
                        "更大檔案上傳限制",
                        "優先支援服務",
                        "進階功能存取",
                    ],
                )
            else:
                response.upgrade_suggestion = UpgradeSuggestion(
                    plan_id="ENTERPRISE",
                    display_name="企業方案",
                    benefits=[
                        "無限音檔處理額度",
                        "最大檔案上傳限制",
                        "專屬客戶支援",
                        "客製化整合功能",
                    ],
                )

        logger.info(
            f"Validation for user {current_user.id}: action={request.action}, allowed={response.allowed}"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error validating action for user {current_user.id}: {str(e)}"
        )
        # Fail open - allow action on error for better UX
        return ValidateActionResponse(
            allowed=True,
            message="Validation temporarily unavailable, proceeding with action",
            limit_info=None,
            upgrade_suggestion=None,
        )


@router.get("/current-usage")
async def get_current_usage(
    current_user: User = Depends(get_current_user_dependency),
    plan_retrieval_use_case: PlanRetrievalUseCase = Depends(get_plan_retrieval_use_case),
) -> Dict[str, Any]:
    """Get current usage statistics for the authenticated user using Clean Architecture."""
    try:
        # Get user's current plan information using the use case
        plan_info = plan_retrieval_use_case.get_user_current_plan(current_user.id)

        # Calculate reset date
        now = datetime.utcnow()
        if now.month == 12:
            reset_date = datetime(now.year + 1, 1, 1)
        else:
            reset_date = datetime(now.year, now.month + 1, 1)

        # Get plan limits from the plan configuration
        plan_limits = plan_info.get("limits", {})

        return {
            "plan": plan_info.get("id", "FREE"),
            "usage": {
                # Phase 2: Only minutes-based limits, sessions/transcriptions unlimited
                "minutes": {
                    "current": current_user.usage_minutes or 0,
                    "limit": plan_limits.get("maxTotalMinutes", -1),
                    "percentage": calculate_percentage(
                        current_user.usage_minutes or 0,
                        plan_limits.get("maxTotalMinutes", -1),
                    ),
                },
                "file_size_mb": {"limit": plan_limits.get("maxFileSizeMb", 60)},
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
    usage_log_use_case: CreateUsageLogUseCase = Depends(get_usage_log_use_case),
) -> Dict[str, Any]:
    """
    Increment usage counter for a specific metric using Clean Architecture.
    This endpoint is typically called after a successful action.

    Metrics: session_count, transcription_count, usage_minutes
    """
    try:
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

        # Create usage log entry through use case
        usage_log_use_case.log_usage(
            user_id=current_user.id,
            action=metric,
            usage_data={"amount": amount, "metric": metric}
        )

        # For backward compatibility, we'll simulate the old behavior
        # In a full Clean Architecture implementation, we'd have a separate
        # UserStatsUpdateUseCase that would handle the user model updates

        # Update user model directly for now (legacy compatibility)
        if metric == "session_count":
            current_user.session_count = (current_user.session_count or 0) + amount
        elif metric == "transcription_count":
            current_user.transcription_count = (current_user.transcription_count or 0) + amount
        elif metric == "usage_minutes":
            current_user.usage_minutes = (current_user.usage_minutes or 0) + amount

        # Get the new value for response
        if metric == "session_count":
            new_value = current_user.session_count
        elif metric == "transcription_count":
            new_value = current_user.transcription_count
        else:  # usage_minutes
            new_value = current_user.usage_minutes

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
    admin_key: str,
    user_usage_use_case: GetUserUsageUseCase = Depends(get_user_usage_use_case)
) -> Dict[str, Any]:
    """
    Reset monthly usage counters for all users using Clean Architecture.
    This endpoint should be called by a scheduled job at the start of each month.
    Requires admin key for security.
    """
    # Verify admin key
    if admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin key"
        )

    try:
        # Use dedicated BulkUsageResetUseCase for bulk operations
        from ...core.services.bulk_operations_use_case import BulkUsageResetUseCase
        from ...infrastructure.factories import RepositoryFactory

        # Create use case with repository dependencies
        usage_history_repo = RepositoryFactory.create_usage_log_repository(db)
        user_repo = RepositoryFactory.create_user_repository(db)
        bulk_reset_use_case = BulkUsageResetUseCase(usage_history_repo, user_repo)

        # Execute bulk usage reset
        reset_result = bulk_reset_use_case.reset_all_monthly_usage()

        if reset_result["success"]:
            logger.info(f"✅ Reset monthly usage for {reset_result['users_reset']} users")
        else:
            logger.error(f"❌ Bulk usage reset failed: {reset_result.get('error', 'Unknown error')}")

        reset_count = reset_result.get("users_reset", 0)

        return {
            **reset_result,  # Include all results from use case
            "reset_time": datetime.utcnow().isoformat() + "Z"
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
