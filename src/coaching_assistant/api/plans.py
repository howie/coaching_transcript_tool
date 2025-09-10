"""API endpoints for plan management and usage limits."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import logging

from ..core.database import get_db
from ..api.auth import get_current_user_dependency
from ..models.user import User, UserPlan
from ..models.plan_configuration import PlanConfiguration
from ..models.ecpay_subscription import (
    SaasSubscription,
)
from ..services.usage_tracking import PlanLimits

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/plans", tags=["plans"])


def get_plan_config_from_db(
    db: Session, plan_type: UserPlan
) -> Dict[str, Any]:
    """Get plan configuration from database."""
    plan_config = (
        db.query(PlanConfiguration)
        .filter(PlanConfiguration.plan_type == plan_type)
        .first()
    )

    if not plan_config:
        logger.warning(
            f"Plan configuration not found for {plan_type}, using fallback"
        )
        # Fallback to hardcoded config if not found in DB
        return PLAN_CONFIGS[plan_type].copy()

    # Convert database model to API format
    limits = plan_config.limits.copy()

    # Map database keys to API keys for consistency
    api_limits = {
        "maxSessions": limits.get("maxSessions", -1),
        "maxTotalMinutes": limits.get("maxMinutes", -1),
        "maxTranscriptionCount": limits.get("maxTranscriptions", -1),
        "maxFileSizeMb": limits.get("maxFileSize", 60),
        "exportFormats": ["json", "txt"],  # Default formats
        "concurrentProcessing": limits.get("concurrentJobs", 1),
        "retentionDays": limits.get("retentionDays", 30),
    }

    # Convert -1 to "unlimited" for frontend display
    if api_limits["maxSessions"] == -1:
        api_limits["maxSessions"] = "unlimited"
    if api_limits["maxTotalMinutes"] == -1:
        api_limits["maxTotalMinutes"] = "unlimited"
    if api_limits["maxTranscriptionCount"] == -1:
        api_limits["maxTranscriptionCount"] = "unlimited"
    if api_limits["retentionDays"] == -1:
        api_limits["retentionDays"] = "permanent"

    return {
        "planName": plan_config.plan_name,
        "displayName": plan_config.display_name,
        "description": plan_config.description,
        "tagline": plan_config.tagline,
        "limits": api_limits,
        "features": plan_config.features or {},
        "pricing": {
            "monthlyUsd": plan_config.monthly_price_cents / 100,
            "annualUsd": plan_config.annual_price_cents / 100,
            "monthlyTwd": plan_config.monthly_price_twd_cents / 100,
            "annualTwd": plan_config.annual_price_twd_cents / 100,
            "annualDiscountPercentage": plan_config._calculate_annual_discount(),
            "annualSavingsUsd": plan_config._calculate_annual_savings(),
            "currency": plan_config.currency,
        },
        "display": {
            "isPopular": plan_config.is_popular,
            "colorScheme": plan_config.color_scheme,
            "sortOrder": plan_config.sort_order,
        },
    }


# Plan configurations - DEPRECATED: now using database, keeping as fallback
PLAN_CONFIGS = {
    UserPlan.FREE: {
        "planName": "free",
        "displayName": "Free Trial",
        "description": "Perfect for trying out the platform",
        "tagline": "Get started for free",
        "limits": {
            "maxSessions": 10,
            "maxTotalMinutes": 120,
            "maxTranscriptionCount": 20,
            "maxFileSizeMb": 50,
            "exportFormats": ["json", "txt"],
            "concurrentProcessing": 1,
            "retentionDays": 30,
        },
        "features": {
            "prioritySupport": False,
            "exportFormats": ["json", "txt"],
            "concurrentProcessing": 1,
        },
        "pricing": {
            "monthlyUsd": 0,
            "annualUsd": 0,
            "annualDiscountPercentage": 0,
            "annualSavingsUsd": 0,
        },
        "display": {"isPopular": False, "colorScheme": "gray", "sortOrder": 1},
    },
    UserPlan.PRO: {
        "planName": "pro",
        "displayName": "Pro Plan",
        "description": "For professional coaches",
        "tagline": "Most popular choice",
        "limits": {
            "maxSessions": 100,
            "maxTotalMinutes": 1200,
            "maxTranscriptionCount": 200,
            "maxFileSizeMb": 200,
            "exportFormats": ["json", "txt", "vtt", "srt"],
            "concurrentProcessing": 3,
            "retentionDays": 365,
        },
        "features": {
            "prioritySupport": True,
            "exportFormats": ["json", "txt", "vtt", "srt"],
            "concurrentProcessing": 3,
        },
        "pricing": {
            "monthlyUsd": 29.99,
            "annualUsd": 24.99,
            "annualDiscountPercentage": 17,
            "annualSavingsUsd": 60,
        },
        "display": {"isPopular": True, "colorScheme": "blue", "sortOrder": 2},
    },
    UserPlan.ENTERPRISE: {
        "planName": "business",
        "displayName": "Business Plan",
        "description": "For coaching organizations",
        "tagline": "Scale your team",
        "limits": {
            "maxSessions": "unlimited",
            "maxTotalMinutes": "unlimited",
            "maxTranscriptionCount": "unlimited",
            "maxFileSizeMb": 500,
            "exportFormats": ["json", "txt", "vtt", "srt", "xlsx"],
            "concurrentProcessing": 10,
            "retentionDays": "permanent",
        },
        "features": {
            "prioritySupport": True,
            "exportFormats": ["json", "txt", "vtt", "srt", "xlsx"],
            "concurrentProcessing": 10,
        },
        "pricing": {
            "monthlyUsd": 99.99,
            "annualUsd": 83.33,
            "annualDiscountPercentage": 17,
            "annualSavingsUsd": 200,
        },
        "display": {
            "isPopular": False,
            "colorScheme": "purple",
            "sortOrder": 3,
        },
    },
}


@router.get("/")
async def get_available_plans(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get all available billing plans with features and pricing."""

    logger.info("📋 Fetching available plans from database")

    plans = []
    for plan_enum in [UserPlan.FREE, UserPlan.PRO, UserPlan.ENTERPRISE]:
        config = get_plan_config_from_db(db, plan_enum)
        # Convert unlimited values for frontend consistency
        if config["limits"]["maxSessions"] == "unlimited":
            config["limits"]["maxSessions"] = -1
        if config["limits"]["maxTotalMinutes"] == "unlimited":
            config["limits"]["maxTotalMinutes"] = -1
        if config["limits"]["maxTranscriptionCount"] == "unlimited":
            config["limits"]["maxTranscriptionCount"] = -1
        if config["limits"]["retentionDays"] == "permanent":
            config["limits"]["retentionDays"] = -1
        plans.append(config)

    return {
        "plans": plans,
        "currency": "TWD",  # Updated to TWD
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


@router.get("/current")
async def get_current_plan_status(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get current user's plan details and usage status."""

    logger.info(f"📊 User {current_user.id} requesting current plan status")

    # Get plan configuration from database
    plan_config = get_plan_config_from_db(db, current_user.plan)

    # Convert unlimited values
    if plan_config["limits"]["maxSessions"] == "unlimited":
        plan_config["limits"]["maxSessions"] = -1
    if plan_config["limits"]["maxTotalMinutes"] == "unlimited":
        plan_config["limits"]["maxTotalMinutes"] = -1
    if plan_config["limits"]["maxTranscriptionCount"] == "unlimited":
        plan_config["limits"]["maxTranscriptionCount"] = -1
    if plan_config["limits"]["retentionDays"] == "permanent":
        plan_config["limits"]["retentionDays"] = -1

    # Calculate usage percentages
    def calc_percentage(current: float, limit: float) -> float | None:
        if limit == -1 or limit == float("inf"):
            return None
        return round((current / limit * 100), 2) if limit > 0 else 0

    # Get plan limits from service
    plan_limits = PlanLimits.get_limits(current_user.plan)
    max_minutes = plan_limits["minutes_per_month"]
    if max_minutes == float("inf"):
        max_minutes = -1

    # Build usage status
    usage_status = {
        "userId": str(current_user.id),
        "plan": current_user.plan.value,
        "planDisplayName": plan_config["displayName"],
        "currentUsage": {
            "sessions": current_user.session_count,
            "minutes": current_user.usage_minutes,
            "transcriptions": current_user.transcription_count,
        },
        "planLimits": plan_config["limits"],
        "usagePercentages": {
            "sessions": calc_percentage(
                current_user.session_count,
                plan_config["limits"]["maxSessions"],
            ),
            "minutes": calc_percentage(
                current_user.usage_minutes, max_minutes
            ),
            "transcriptions": calc_percentage(
                current_user.transcription_count,
                plan_config["limits"]["maxTranscriptionCount"],
            ),
        },
        "approachingLimits": {
            "sessions": (
                calc_percentage(
                    current_user.session_count,
                    plan_config["limits"]["maxSessions"],
                )
                or 0
            )
            >= 80,
            "minutes": (
                calc_percentage(current_user.usage_minutes, max_minutes) or 0
            )
            >= 80,
            "transcriptions": (
                calc_percentage(
                    current_user.transcription_count,
                    plan_config["limits"]["maxTranscriptionCount"],
                )
                or 0
            )
            >= 80,
        },
        "nextReset": None,
    }

    # Calculate next reset date (first day of next month)
    if current_user.current_month_start:
        next_month = current_user.current_month_start.replace(day=1)
        if next_month.month == 12:
            next_month = next_month.replace(year=next_month.year + 1, month=1)
        else:
            next_month = next_month.replace(month=next_month.month + 1)
        usage_status["nextReset"] = next_month.isoformat()

    # Add upgrade suggestion if approaching limits
    if (
        any(usage_status["approachingLimits"].values())
        and current_user.plan != UserPlan.ENTERPRISE
    ):
        suggested_plan = (
            UserPlan.PRO
            if current_user.plan == UserPlan.FREE
            else UserPlan.ENTERPRISE
        )
        suggested_config = PLAN_CONFIGS[suggested_plan]
        usage_status["upgradeSuggestion"] = {
            "suggestedPlan": suggested_config["planName"],
            "displayName": suggested_config["displayName"],
            "keyBenefits": _get_upgrade_benefits(
                current_user.plan, suggested_plan
            ),
            "pricing": suggested_config["pricing"],
            "tagline": suggested_config["tagline"],
        }

    # Build subscription info from actual subscription data
    subscription_info = {
        "startDate": (
            current_user.created_at.isoformat()
            if current_user.created_at
            else None
        ),
        "endDate": None,
        "active": current_user.plan
        != UserPlan.FREE,  # More accurate active status
        "stripeSubscriptionId": None,
    }

    # Get actual subscription data if user has paid plan
    if current_user.plan != UserPlan.FREE:
        active_subscription = (
            db.query(SaasSubscription)
            .filter(
                SaasSubscription.user_id == current_user.id,
                SaasSubscription.status.in_(["active", "past_due"]),
            )
            .first()
        )

        if active_subscription:
            subscription_info.update(
                {
                    "active": active_subscription.status == "active",
                    "startDate": active_subscription.current_period_start.isoformat(),
                    "endDate": active_subscription.current_period_end.isoformat(),
                    "subscriptionId": str(active_subscription.id),
                    "planId": active_subscription.plan_id,
                    "billingCycle": active_subscription.billing_cycle,
                    "status": active_subscription.status,
                    "nextPaymentDate": None,
                }
            )

            # Get next payment date from authorization record
            if (
                active_subscription.auth_record
                and active_subscription.auth_record.next_pay_date
            ):
                subscription_info["nextPaymentDate"] = (
                    active_subscription.auth_record.next_pay_date.isoformat()
                )
        else:
            # User has paid plan in database but no active subscription
            subscription_info["active"] = False
            logger.warning(
                f"User {current_user.id} has plan {current_user.plan} but no active subscription"
            )

    return {
        "currentPlan": plan_config,
        "usageStatus": usage_status,
        "subscriptionInfo": subscription_info,
    }


@router.get("/compare")
async def compare_plans(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get plan comparison focused on upgrade paths."""

    logger.info(f"📊 User {current_user.id} requesting plan comparison")

    # Get all plans
    all_plans_response = await get_available_plans(db)
    all_plans = all_plans_response["plans"]

    # Mark current plan
    for plan in all_plans:
        if plan["planName"] == current_user.plan.value.lower().replace(
            "enterprise", "business"
        ):
            plan["isCurrent"] = True
        else:
            plan["isCurrent"] = False

    # Get upgrade suggestion
    recommended_upgrade = None
    if current_user.plan != UserPlan.ENTERPRISE:
        suggested_plan = (
            UserPlan.PRO
            if current_user.plan == UserPlan.FREE
            else UserPlan.ENTERPRISE
        )
        suggested_config = PLAN_CONFIGS[suggested_plan]
        recommended_upgrade = {
            "suggestedPlan": suggested_config["planName"],
            "displayName": suggested_config["displayName"],
            "keyBenefits": _get_upgrade_benefits(
                current_user.plan, suggested_plan
            ),
            "pricing": suggested_config["pricing"],
            "tagline": suggested_config["tagline"],
        }

    return {
        "currentPlan": current_user.plan.value,
        "plans": all_plans,
        "recommendedUpgrade": recommended_upgrade,
    }


@router.post("/validate")
async def validate_action(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Validate if user can perform action within plan limits."""

    action = request.get("action")
    logger.info(f"🔍 Validating action '{action}' for user {current_user.id}")

    # Get plan limits from database
    plan_config = get_plan_config_from_db(db, current_user.plan)
    limits = plan_config["limits"]

    validation_result = {
        "allowed": True,
        "message": "Action permitted",
        "limitInfo": None,
        "upgradeSuggestion": None,
    }

    if action == "create_session":
        max_sessions = limits["maxSessions"]
        if (
            max_sessions != "unlimited"
            and max_sessions != -1
            and current_user.session_count >= max_sessions
        ):
            validation_result.update(
                {
                    "allowed": False,
                    "message": f"Session limit exceeded ({max_sessions} sessions per month)",
                    "limitInfo": {
                        "type": "maxSessions",
                        "current": current_user.session_count,
                        "limit": max_sessions,
                    },
                }
            )

    elif action == "upload_file":
        file_size_mb = request.get("file_size_mb", 0)
        if file_size_mb > limits["maxFileSizeMb"]:
            validation_result.update(
                {
                    "allowed": False,
                    "message": f"File size exceeds limit ({limits['maxFileSizeMb']}MB)",
                    "limitInfo": {
                        "type": "maxFileSizeMb",
                        "current": file_size_mb,
                        "limit": limits["maxFileSizeMb"],
                    },
                }
            )

    elif action == "export_transcript":
        export_format = request.get("format", "").lower()
        if export_format not in limits["exportFormats"]:
            validation_result.update(
                {
                    "allowed": False,
                    "message": f"Export format '{export_format}' not available on {current_user.plan.value} plan",
                    "limitInfo": {
                        "type": "exportFormats",
                        "requested": export_format,
                        "available": limits["exportFormats"],
                    },
                }
            )

    elif action == "transcribe":
        max_transcriptions = limits["maxTranscriptionCount"]
        if (
            max_transcriptions != "unlimited"
            and max_transcriptions != -1
            and current_user.transcription_count >= max_transcriptions
        ):
            validation_result.update(
                {
                    "allowed": False,
                    "message": f"Transcription limit exceeded ({max_transcriptions} transcriptions per month)",
                    "limitInfo": {
                        "type": "maxTranscriptionCount",
                        "current": current_user.transcription_count,
                        "limit": max_transcriptions,
                    },
                }
            )

    # Add upgrade suggestion if action is blocked
    if (
        not validation_result["allowed"]
        and current_user.plan != UserPlan.ENTERPRISE
    ):
        suggested_plan = (
            UserPlan.PRO
            if current_user.plan == UserPlan.FREE
            else UserPlan.ENTERPRISE
        )
        suggested_config = PLAN_CONFIGS[suggested_plan]
        validation_result["upgradeSuggestion"] = {
            "suggestedPlan": suggested_config["planName"],
            "displayName": suggested_config["displayName"],
            "pricing": suggested_config["pricing"],
        }

    return validation_result


def _get_upgrade_benefits(
    current_plan: UserPlan, suggested_plan: UserPlan
) -> List[str]:
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
