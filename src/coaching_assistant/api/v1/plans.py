"""Plans management API endpoints - Consolidated version."""

import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
# Removed direct database dependencies for Clean Architecture compliance
from .auth import get_current_user_dependency
from .dependencies import (
    get_plan_retrieval_use_case,
    get_plan_validation_use_case,
    get_subscription_retrieval_use_case,
)
from ...models import User
from ...models.user import UserPlan
from ...core.services.plan_management_use_case import (
    PlanRetrievalUseCase,
    PlanValidationUseCase,
)
from ...core.services.subscription_management_use_case import (
    SubscriptionRetrievalUseCase,
)
from ...exceptions import DomainException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Plans"])


# Helper function to safely get plan value
def _get_plan_value(plan):
    """Safely get the string value from a plan field, handling both enum and string types."""
    return plan.value if hasattr(plan, 'value') else plan


# Pydantic models for v1 API
class PlanLimits(BaseModel):
    max_total_minutes: int  # Only limit based on minutes
    max_file_size_mb: int


class PlanPricing(BaseModel):
    monthly_twd: int  # Amount in cents
    annual_twd: int  # Amount in cents
    monthly_usd: int  # Amount in cents
    annual_usd: int  # Amount in cents


class PlanResponse(BaseModel):
    id: str
    name: str
    display_name: str
    description: str
    pricing: PlanPricing
    features: List[str]
    limits: PlanLimits
    is_active: bool
    sort_order: int


class PlansListResponse(BaseModel):
    plans: List[PlanResponse]
    total: int


# Direct database access functions removed - use injected use cases instead


def _get_upgrade_benefits(current_plan: UserPlan, suggested_plan: UserPlan) -> List[str]:
    """Get key benefits of upgrading to suggested plan."""
    benefits = {
        (UserPlan.FREE, UserPlan.PRO): [
            "10x more sessions (100 vs 10)",
            "10x more audio time (20 hours vs 2 hours)",
            "All export formats (VTT, SRT)",
            "Priority support",
            "1 year data retention",
        ],
        (UserPlan.PRO, UserPlan.ENTERPRISE): [
            "Unlimited sessions and audio",
            "Advanced export formats (XLSX)",
            "10 concurrent processing slots",
            "Permanent data retention",
            "Premium support with SLA",
        ],
        (UserPlan.FREE, UserPlan.ENTERPRISE): [
            "Unlimited everything",
            "All export formats including XLSX",
            "10 concurrent processing slots",
            "Permanent data retention",
            "Premium support with SLA",
        ],
    }
    return benefits.get((current_plan, suggested_plan), [])


# Hardcoded plan configurations removed - now using repository pattern through use cases


# V1 API Endpoints (newer plan system)
@router.get("", response_model=PlansListResponse)
async def get_available_plans_v1(
    current_user: User = Depends(get_current_user_dependency),
    plan_retrieval_use_case: PlanRetrievalUseCase = Depends(get_plan_retrieval_use_case),
):
    """Get all available subscription plans (V1 API using Clean Architecture)."""
    try:
        # Use plan retrieval use case to get all plans
        plans_data = plan_retrieval_use_case.get_all_plans()

        # Convert to PlanResponse format
        converted_plans = []
        for plan_data in plans_data:
            # Convert the use case format to API response format
            plan_response = PlanResponse(
                id=str(plan_data["id"]).upper(),
                name=plan_data["name"],
                display_name=plan_data["display_name"],
                description=plan_data["description"],
                pricing=PlanPricing(
                    monthly_twd=int(plan_data["pricing"]["monthly_twd"] * 100),  # Convert to cents
                    annual_twd=int(plan_data["pricing"]["annual_twd"] * 100),
                    monthly_usd=int(plan_data["pricing"]["monthly_usd"] * 100),
                    annual_usd=int(plan_data["pricing"]["annual_usd"] * 100),
                ),
                features=plan_data.get("features", {}).get("list", []) if isinstance(plan_data.get("features"), dict) else plan_data.get("features", []),
                limits=PlanLimits(
                    max_total_minutes=plan_data["limits"]["maxTotalMinutes"] if plan_data["limits"]["maxTotalMinutes"] != "unlimited" else -1,
                    max_file_size_mb=plan_data["limits"]["maxFileSizeMb"],
                ),
                is_active=plan_data.get("is_active", True),
                sort_order=plan_data.get("sort_order", 999),
            )
            converted_plans.append(plan_response)

        logger.info(f"Retrieved {len(converted_plans)} plans for user {current_user.id}")
        return PlansListResponse(plans=converted_plans, total=len(converted_plans))

    except Exception as e:
        logger.error(f"Failed to get available plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available plans.",
        )


@router.get("/current")
async def get_current_plan_status(
    current_user: User = Depends(get_current_user_dependency),
    plan_retrieval_use_case: PlanRetrievalUseCase = Depends(get_plan_retrieval_use_case),
    plan_validation_use_case: PlanValidationUseCase = Depends(get_plan_validation_use_case),
    subscription_retrieval_use_case: SubscriptionRetrievalUseCase = Depends(get_subscription_retrieval_use_case),
) -> Dict[str, Any]:
    """Get current user's plan details and usage status."""
    logger.info(f"📊 User {current_user.id} requesting current plan status")

    try:
        # Get plan configuration through use case
        plan_info = plan_retrieval_use_case.get_user_current_plan(current_user.id)

        # Get usage validation information
        usage_validation = plan_validation_use_case.validate_user_limits(current_user.id)

        # Build usage status from validation results
        current_usage = usage_validation["current_usage"]
        limits = usage_validation["limits"]

        # Calculate usage percentages
        def calc_percentage(current: float, limit: float) -> float | None:
            if limit == -1 or limit == float("inf") or not isinstance(limit, (int, float)):
                return None
            return round((current / limit * 100), 2) if limit > 0 else 0

        # Convert limits format for API compatibility
        formatted_limits = {
            "maxSessions": limits.get("maxSessions", -1),
            "maxTotalMinutes": limits.get("maxMinutes", -1),
            "maxTranscriptionCount": limits.get("maxTranscriptions", -1),
            "maxFileSizeMb": limits.get("maxFileSize", 60),
            "exportFormats": limits.get("exportFormats", ["json", "txt"]),
            "concurrentProcessing": limits.get("concurrentJobs", 1),
            "retentionDays": limits.get("retentionDays", 30),
        }

        usage_status = {
            "userId": str(current_user.id),
            "plan": _get_plan_value(current_user.plan),
            "planDisplayName": plan_info.get("display_name", _get_plan_value(current_user.plan)),
            "currentUsage": {
                "sessions": current_usage["session_count"],
                "minutes": current_usage["total_minutes"],
                "transcriptions": current_user.transcription_count,  # Keep from user model for now
            },
            "planLimits": formatted_limits,
            "usagePercentages": {
                "sessions": calc_percentage(
                    current_usage["session_count"],
                    formatted_limits["maxSessions"],
                ),
                "minutes": calc_percentage(
                    current_usage["total_minutes"],
                    formatted_limits["maxTotalMinutes"]
                ),
                "transcriptions": calc_percentage(
                    current_user.transcription_count,
                    formatted_limits["maxTranscriptionCount"],
                ),
            },
            "approachingLimits": {
                "sessions": len([w for w in usage_validation["warnings"] if w["type"] == "session_count_warning"]) > 0,
                "minutes": len([w for w in usage_validation["warnings"] if w["type"] == "minutes_warning"]) > 0,
                "transcriptions": False,  # Not implemented in use case yet
            },
            "nextReset": current_usage.get("period_start"),  # Use period info from use case
        }

        # Add upgrade suggestion if approaching limits using Clean Architecture
        if (
            any(usage_status["approachingLimits"].values())
            and _get_plan_value(current_user.plan) != UserPlan.ENTERPRISE.value
        ):
            try:
                # Get all plans to find the suggested upgrade plan
                all_plans = plan_retrieval_use_case.get_all_plans()
                suggested_plan_id = (
                    "PRO"
                    if _get_plan_value(current_user.plan) == UserPlan.FREE.value
                    else "ENTERPRISE"
                )

                # Find the suggested plan from the available plans
                suggested_config = None
                for plan in all_plans:
                    if plan["id"] == suggested_plan_id:
                        suggested_config = plan
                        break

                if suggested_config:
                    usage_status["upgradeSuggestion"] = {
                        "suggestedPlan": suggested_config["name"],
                        "displayName": suggested_config["display_name"],
                        "keyBenefits": _get_upgrade_benefits(current_user.plan, getattr(UserPlan, suggested_plan_id)),
                        "pricing": suggested_config["pricing"],
                        "tagline": suggested_config.get("tagline", "Upgrade for more features"),
                    }
            except Exception as e:
                logger.warning(f"Could not generate upgrade suggestion: {e}")
                # Continue without upgrade suggestion

        # Build subscription info from actual subscription data
        subscription_info = {
            "startDate": (
                current_user.created_at.isoformat() if current_user.created_at else None
            ),
            "endDate": None,
            "active": _get_plan_value(current_user.plan) != UserPlan.FREE.value,  # More accurate active status
            "stripeSubscriptionId": None,
        }

        # Get actual subscription data if user has paid plan with graceful error handling
        if _get_plan_value(current_user.plan) != UserPlan.FREE.value:
            try:
                subscription_data = subscription_retrieval_use_case.get_current_subscription(current_user.id)

                if subscription_data.get("subscription"):
                    sub = subscription_data["subscription"]
                    subscription_info.update(
                        {
                            "active": sub.get("status") in ["active", "past_due"],
                            "startDate": sub.get("created_at"),
                            "endDate": sub.get("next_billing_date"),
                            "subscriptionId": sub.get("id"),
                            "planId": sub.get("plan_id"),
                            "billingCycle": sub.get("billing_cycle"),
                            "status": sub.get("status"),
                            "nextPaymentDate": sub.get("next_billing_date"),
                        }
                    )
                else:
                    # User has paid plan in database but no active subscription
                    subscription_info["active"] = False
                    logger.warning(
                        f"User {current_user.id} has plan {_get_plan_value(current_user.plan)} but no active subscription"
                    )
            except DomainException as e:
                logger.warning(f"Subscription service returned domain error for user {current_user.id}: {e}")
                subscription_info["active"] = False
                # Continue with basic plan info - subscription error is not critical
            except Exception as e:
                logger.error(f"Critical error retrieving subscription for user {current_user.id}: {e}")
                subscription_info["active"] = False
                # Continue with basic plan info - subscription error should not break plans endpoint

        return {
            "currentPlan": plan_info,
            "usageStatus": usage_status,
            "subscriptionInfo": subscription_info,
        }

    except DomainException as e:
        logger.warning(f"User not found when retrieving plan status: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    except RuntimeError as e:
        logger.error(f"Database connection error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error"
        )
    except Exception as e:
        logger.error(f"Failed to get current plan status for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve current plan status"
        )


@router.get("/compare")
async def compare_plans(
    current_user: User = Depends(get_current_user_dependency),
    plan_retrieval_use_case: PlanRetrievalUseCase = Depends(get_plan_retrieval_use_case),
) -> Dict[str, Any]:
    """Get plan comparison focused on upgrade paths."""
    logger.info(f"📊 User {current_user.id} requesting plan comparison")

    try:
        # Get all plans using the use case
        all_plans_response = await get_available_plans_legacy(plan_retrieval_use_case)
        all_plans = all_plans_response["plans"]

        # Mark current plan
        current_plan_value = _get_plan_value(current_user.plan).lower()
        for plan in all_plans:
            plan_name = plan["planName"].lower()
            # Handle enterprise/business naming variation
            if current_plan_value == "enterprise":
                current_plan_value = "business"

            plan["isCurrent"] = plan_name == current_plan_value

        # Get comparison data through use case
        comparison_data = plan_retrieval_use_case.compare_plans()
        logger.debug(f"Retrieved comparison data with {comparison_data.get('total_plans', 0)} plans")

        # Simple upgrade recommendation based on current plan
        recommended_upgrade = None
        current_plan_enum = getattr(current_user.plan, 'value', current_user.plan) if hasattr(current_user.plan, 'value') else current_user.plan

        if current_plan_enum != "ENTERPRISE":
            # Find next tier plan for upgrade suggestion
            if current_plan_enum == "FREE":
                suggested_plan_name = "PRO"
                suggested_display_name = "Pro Plan"
                key_benefits = [
                    "10x more sessions",
                    "10x more audio time",
                    "All export formats",
                    "Priority support"
                ]
            else:  # PRO or other
                suggested_plan_name = "ENTERPRISE"
                suggested_display_name = "Enterprise Plan"
                key_benefits = [
                    "Unlimited sessions and audio",
                    "Advanced export formats",
                    "Premium support"
                ]

            recommended_upgrade = {
                "suggestedPlan": suggested_plan_name.lower(),
                "displayName": suggested_display_name,
                "keyBenefits": key_benefits,
                "pricing": {"monthlyUsd": 29.99 if suggested_plan_name == "PRO" else 99.99},
                "tagline": "Best choice for professional coaches"
            }

        return {
            "currentPlan": current_plan_value,
            "plans": all_plans,
            "recommendedUpgrade": recommended_upgrade,
        }
    except Exception as e:
        logger.error(f"Failed to compare plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plan comparison"
        )


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan_by_id(
    plan_id: str,
    current_user: User = Depends(get_current_user_dependency),
    plan_retrieval_use_case: PlanRetrievalUseCase = Depends(get_plan_retrieval_use_case),
):
    """Get specific plan by ID."""
    try:
        # Get all plans and find the requested one
        plans_response = await get_available_plans_v1(current_user, plan_retrieval_use_case)

        for plan in plans_response.plans:
            if plan.id == plan_id.upper():
                return plan

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan {plan_id} not found.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get plan {plan_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plan information.",
        )


# Legacy API Endpoints (original plan system - for backwards compatibility)
@router.get("/legacy")
async def get_available_plans_legacy(
    plan_retrieval_use_case: PlanRetrievalUseCase = Depends(get_plan_retrieval_use_case),
) -> Dict[str, Any]:
    """Get all available billing plans with features and pricing (Legacy API)."""
    logger.info("📋 Fetching available plans using Clean Architecture")

    try:
        plans_data = plan_retrieval_use_case.get_all_plans()

        # Convert to legacy format for backward compatibility
        legacy_plans = []
        for plan_data in plans_data:
            legacy_format = {
                "planName": plan_data["name"].lower(),
                "displayName": plan_data["display_name"],
                "description": plan_data["description"],
                "tagline": plan_data.get("tagline", ""),
                "limits": {
                    "maxSessions": -1 if plan_data["limits"]["maxTotalMinutes"] == "unlimited" else 999,  # Legacy compatibility
                    "maxTotalMinutes": -1 if plan_data["limits"]["maxTotalMinutes"] == "unlimited" else plan_data["limits"]["maxTotalMinutes"],
                    "maxTranscriptionCount": -1,  # Unlimited in new system
                    "maxFileSizeMb": plan_data["limits"]["maxFileSizeMb"],
                    "exportFormats": plan_data["limits"].get("exportFormats", ["json", "txt"]),
                    "concurrentProcessing": plan_data["limits"].get("concurrentProcessing", 1),
                    "retentionDays": plan_data["limits"].get("retentionDays", 30),
                },
                "features": plan_data.get("features", {}),
                "pricing": plan_data["pricing"],
                "display": {
                    "isPopular": plan_data.get("sort_order") == 2,  # Assume middle plan is popular
                    "colorScheme": "blue",
                    "sortOrder": plan_data.get("sort_order", 999),
                },
            }
            legacy_plans.append(legacy_format)

        return {
            "plans": legacy_plans,
            "currency": "TWD",
            "billingCycles": ["monthly", "annual"],
            "featuresComparison": {
                "sessions": "Number of coaching sessions you can upload per month",
                "audioMinutes": "Total minutes of audio you can transcribe per month",
                "transcriptionExports": "Number of transcript exports per month",
                "fileSize": "Maximum size per audio file upload",
                "exportFormats": "Available transcript export formats",
                "concurrentProcessing": "Number of files you can transcribe simultaneously",
                "prioritySupport": "Priority email support with faster response times",
                "dataRetention": "How long your data is stored on our platform",
            },
        }
    except Exception as e:
        logger.error(f"Failed to get legacy plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plans"
        )



@router.post("/validate")
async def validate_action(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user_dependency),
    plan_validation_use_case: PlanValidationUseCase = Depends(get_plan_validation_use_case),
) -> Dict[str, Any]:
    """Validate if user can perform action within plan limits using Clean Architecture."""
    action = request.get("action")
    logger.info(f"🔍 Validating action '{action}' for user {current_user.id}")

    try:
        # Use plan validation use case for business logic
        if action == "upload_file":
            file_size_mb = request.get("file_size_mb", 0)
            file_validation = plan_validation_use_case.validate_file_size(current_user.id, file_size_mb)

            validation_result = {
                "allowed": file_validation["valid"],
                "message": file_validation["message"],
                "limitInfo": {
                    "type": "maxFileSizeMb",
                    "current": file_validation.get("actual", file_size_mb),
                    "limit": file_validation.get("limit", 60),
                } if not file_validation["valid"] else None,
                "upgradeSuggestion": None,
            }
        else:
            # For other actions, use general usage validation
            usage_validation = plan_validation_use_case.validate_user_limits(current_user.id)

            validation_result = {
                "allowed": usage_validation["valid"],
                "message": usage_validation.get("message", "Action permitted"),
                "limitInfo": None,
                "upgradeSuggestion": None,
            }

            # Add specific limit info based on action
            if not usage_validation["valid"] and usage_validation["violations"]:
                # Take the first violation for limit info
                violation = usage_validation["violations"][0]
                validation_result["limitInfo"] = {
                    "type": violation["type"],
                    "current": violation["current"],
                    "limit": violation["limit"],
                }
                validation_result["message"] = violation["message"]

        # Add upgrade suggestion if action is blocked
        current_plan_value = _get_plan_value(current_user.plan)
        if not validation_result["allowed"] and current_plan_value != UserPlan.ENTERPRISE.value:
            if current_plan_value == UserPlan.FREE.value:
                validation_result["upgradeSuggestion"] = {
                    "suggestedPlan": "pro",
                    "displayName": "Pro Plan",
                    "pricing": {"monthlyUsd": 29.99},
                }
            else:
                validation_result["upgradeSuggestion"] = {
                    "suggestedPlan": "enterprise",
                    "displayName": "Enterprise Plan",
                    "pricing": {"monthlyUsd": 99.99},
                }

        return validation_result

    except Exception as e:
        logger.error(f"Error validating action for user {current_user.id}: {e}")
        # Fail open - allow action on error for better UX
        return {
            "allowed": True,
            "message": "Validation temporarily unavailable, action permitted",
            "limitInfo": None,
            "upgradeSuggestion": None,
        }
