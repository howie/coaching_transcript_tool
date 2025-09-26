"""API endpoints for usage tracking and analytics."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from .auth import get_current_user_dependency
from ...api.dependencies import require_admin  # Use the new permission system
from ...core.database import get_db
from ...models.user import User
from ...models.usage_analytics import UsageAnalytics
from ...services.usage_tracking import UsageTrackingService
from .dependencies import get_user_usage_use_case, get_usage_history_use_case, get_user_analytics_use_case, get_admin_analytics_use_case
from ...core.services.usage_tracking_use_case import GetUserUsageUseCase, GetUsageHistoryUseCase, GetUserAnalyticsUseCase, GetAdminAnalyticsUseCase

logger = logging.getLogger(__name__)

router = APIRouter(tags=["usage"])


@router.get("/summary")
async def get_usage_summary(
    current_user: User = Depends(get_current_user_dependency),
    get_user_usage_use_case: GetUserUsageUseCase = Depends(get_user_usage_use_case),
) -> Dict[str, Any]:
    """Get user's comprehensive usage summary.

    Returns current month usage, lifetime totals, recent activity, and monthly trends.
    """

    logger.info(f"📊 User {current_user.id} requesting usage summary")

    try:
        return get_user_usage_use_case.get_current_month_usage(current_user.id)
    except ValueError as e:
        logger.error(f"❌ User error getting usage summary: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ System error getting usage summary: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to get usage summary"
        )


@router.get("/history")
async def get_usage_history(
    months: int = Query(
        3, ge=1, le=12, description="Number of months of history"
    ),
    current_user: User = Depends(get_current_user_dependency),
    get_usage_history_use_case: GetUsageHistoryUseCase = Depends(get_usage_history_use_case),
) -> Dict[str, Any]:
    """Get user's detailed usage history.

    Args:
        months: Number of months of history to retrieve (1-12, default 3)

    Returns detailed usage logs for the specified period.
    """

    logger.info(
        f"📊 User {current_user.id} requesting {months} months of usage history"
    )

    try:
        return get_usage_history_use_case.execute(current_user.id, months)
    except ValueError as e:
        logger.error(f"❌ User error getting usage history: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ System error getting usage history: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to get usage history"
        )


@router.get("/analytics")
async def get_user_analytics(
    current_user: User = Depends(get_current_user_dependency),
    get_user_analytics_use_case: GetUserAnalyticsUseCase = Depends(get_user_analytics_use_case),
) -> Dict[str, Any]:
    """Get user's usage analytics and trends.

    Returns monthly aggregated data for the past 12 months including:
    - Transcription counts by type
    - Minutes processed by provider
    - Cost breakdown
    - Average metrics
    """

    logger.info(f"📊 User {current_user.id} requesting usage analytics")

    try:
        return get_user_analytics_use_case.execute(current_user.id)
    except ValueError as e:
        logger.error(f"❌ User error getting usage analytics: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ System error getting usage analytics: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to get usage analytics"
        )


@router.get("/current-month")
async def get_current_month_usage(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get current month usage details.

    Quick endpoint for checking current month usage against plan limits.
    """

    logger.info(f"📊 User {current_user.id} requesting current month usage")

    # Get plan limits
    from ...services.usage_tracking import PlanLimits

    plan_limits = PlanLimits.get_limits(current_user.plan)

    # Calculate usage percentage
    usage_percentage = (
        (current_user.usage_minutes / plan_limits["minutes_per_month"] * 100)
        if plan_limits["minutes_per_month"] != float("inf")
        else 0
    )

    return {
        "user_id": str(current_user.id),
        "plan": current_user.plan.value,
        "current_month": {
            "usage_minutes": current_user.usage_minutes,
            "session_count": current_user.session_count,
            "transcription_count": current_user.transcription_count,
            "month_start": (
                current_user.current_month_start.isoformat()
                if current_user.current_month_start
                else None
            ),
        },
        "plan_limits": plan_limits,
        "usage_percentage": round(usage_percentage, 2),
        "minutes_remaining": (
            plan_limits["minutes_per_month"] - current_user.usage_minutes
            if plan_limits["minutes_per_month"] != float("inf")
            else float("inf")
        ),
        "can_create_session": current_user.is_usage_within_limit(),
    }


# Admin-only endpoints
@router.get("/admin/analytics")
async def get_admin_usage_analytics(
    start_date: Optional[datetime] = Query(
        None, description="Start date for analytics"
    ),
    end_date: Optional[datetime] = Query(
        None, description="End date for analytics"
    ),
    plan_filter: Optional[str] = Query(
        None, description="Filter by plan (free, pro, enterprise)"
    ),
    admin_user: User = Depends(require_admin),
    get_admin_analytics_use_case: GetAdminAnalyticsUseCase = Depends(get_admin_analytics_use_case),
) -> Dict[str, Any]:
    """Get system-wide usage analytics (Admin only).

    Args:
        start_date: Start date for analytics period (default: 90 days ago)
        end_date: End date for analytics period (default: today)
        plan_filter: Optional filter by user plan

    Returns comprehensive system analytics including:
    - Total usage metrics
    - Plan distribution
    - Provider breakdown
    - Unique users and sessions
    """

    logger.info(f"📊 Admin {admin_user.id} requesting system analytics")

    try:
        return get_admin_analytics_use_case.execute()
    except ValueError as e:
        logger.error(f"❌ Admin error getting analytics: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ System error getting admin analytics: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to get admin analytics"
        )


@router.get("/admin/user/{user_id}")
async def get_specific_user_usage(
    user_id: str,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get usage summary for a specific user (Admin only).

    Args:
        user_id: UUID of the user to get usage for

    Returns the same data as /usage/summary but for any user.
    """

    logger.info(
        f"📊 Admin {admin_user.id} requesting usage for user {user_id}"
    )

    # Verify user exists
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        tracking_service = UsageTrackingService(db)
        return tracking_service.get_user_usage_summary(user_id)
    except Exception as e:
        logger.error(f"❌ Error getting user usage: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user usage")


@router.get("/admin/monthly-report")
async def get_monthly_usage_report(
    month_year: str = Query(..., description="Month in YYYY-MM format"),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get detailed monthly usage report (Admin only).

    Args:
        month_year: Month to get report for in YYYY-MM format

    Returns aggregated data for all users for the specified month.
    """

    logger.info(
        f"📊 Admin {admin_user.id} requesting monthly report for {month_year}"
    )

    # Validate month format
    try:
        datetime.strptime(month_year, "%Y-%m")
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid month format. Use YYYY-MM"
        )

    # Get all analytics for the month
    monthly_analytics = (
        db.query(UsageAnalytics)
        .filter(UsageAnalytics.month_year == month_year)
        .all()
    )

    if not monthly_analytics:
        return {
            "month_year": month_year,
            "message": "No data available for this month",
            "total_users": 0,
            "summary": {},
        }

    # Aggregate data
    total_users = len(monthly_analytics)
    total_transcriptions = sum(
        a.transcriptions_completed for a in monthly_analytics
    )
    total_minutes = sum(
        float(a.total_minutes_processed) for a in monthly_analytics
    )
    total_cost = sum(float(a.total_cost_usd) for a in monthly_analytics)

    # Plan breakdown
    plan_breakdown = {}
    for analytics in monthly_analytics:
        plan = analytics.primary_plan
        if plan not in plan_breakdown:
            plan_breakdown[plan] = {
                "users": 0,
                "transcriptions": 0,
                "minutes": 0.0,
                "cost": 0.0,
            }
        plan_breakdown[plan]["users"] += 1
        plan_breakdown[plan][
            "transcriptions"
        ] += analytics.transcriptions_completed
        plan_breakdown[plan]["minutes"] += float(
            analytics.total_minutes_processed
        )
        plan_breakdown[plan]["cost"] += float(analytics.total_cost_usd)

    # Provider breakdown
    total_google_minutes = sum(
        float(a.google_stt_minutes) for a in monthly_analytics
    )
    total_assemblyai_minutes = sum(
        float(a.assemblyai_minutes) for a in monthly_analytics
    )

    return {
        "month_year": month_year,
        "total_users": total_users,
        "summary": {
            "total_transcriptions": total_transcriptions,
            "total_minutes": total_minutes,
            "total_hours": total_minutes / 60,
            "total_cost_usd": total_cost,
            "avg_minutes_per_user": (
                total_minutes / total_users if total_users > 0 else 0
            ),
            "avg_cost_per_user": (
                total_cost / total_users if total_users > 0 else 0
            ),
        },
        "plan_breakdown": plan_breakdown,
        "provider_breakdown": {
            "google": {
                "minutes": total_google_minutes,
                "percentage": (
                    (total_google_minutes / total_minutes * 100)
                    if total_minutes > 0
                    else 0
                ),
            },
            "assemblyai": {
                "minutes": total_assemblyai_minutes,
                "percentage": (
                    (total_assemblyai_minutes / total_minutes * 100)
                    if total_minutes > 0
                    else 0
                ),
            },
        },
        "period": {
            "start": f"{month_year}-01",
            "end": (
                monthly_analytics[0].period_end.isoformat()
                if monthly_analytics[0].period_end
                else None
            ),
        },
    }
