"""Enhanced billing analytics API endpoints for admin reporting and revenue analysis."""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...core.database import get_db
from ...models.user import User
from ...services.billing_analytics_service import BillingAnalyticsService
from .dependencies import require_admin, require_staff


router = APIRouter(
    prefix="/api/v1/admin/billing-analytics",
    tags=["admin", "billing-analytics"],
)


class BillingAnalyticsResponse(BaseModel):
    """Response model for billing analytics data."""

    id: UUID
    user_id: UUID
    user_email: str
    user_name: str
    period_type: str
    period_start: datetime
    period_end: datetime
    plan_name: str
    total_revenue_usd: float
    total_minutes_processed: float
    plan_utilization_percentage: float
    churn_risk_score: float
    customer_health_score: float
    is_power_user: bool
    is_at_risk: bool


class RevenueMetricsResponse(BaseModel):
    """Response model for revenue metrics."""

    total_revenue: float
    subscription_revenue: float
    overage_revenue: float
    one_time_fees: float
    gross_margin: float
    gross_margin_percentage: float
    avg_revenue_per_user: float
    avg_revenue_per_minute: float


class UsageMetricsResponse(BaseModel):
    """Response model for usage metrics."""

    total_sessions: int
    total_transcriptions: int
    total_minutes: float
    total_hours: float
    avg_session_duration: float
    success_rate: float
    unique_active_users: int


class CustomerSegmentResponse(BaseModel):
    """Response model for customer segmentation."""

    segment: str
    user_count: int
    total_revenue: float
    avg_revenue_per_user: float
    avg_utilization: float
    churn_risk_users: int


class TrendDataPoint(BaseModel):
    """Response model for trend data points."""

    date: str
    revenue: float
    users: int
    sessions: int
    minutes: float
    new_signups: int
    churned_users: int


class AdminAnalyticsOverviewResponse(BaseModel):
    """Response model for admin analytics overview."""

    period_start: datetime
    period_end: datetime
    revenue_metrics: RevenueMetricsResponse
    usage_metrics: UsageMetricsResponse
    customer_segments: List[CustomerSegmentResponse]
    top_users: List[BillingAnalyticsResponse]
    trend_data: List[TrendDataPoint]


class UserAnalyticsDetailResponse(BaseModel):
    """Response model for detailed user analytics."""

    user_id: UUID
    user_email: str
    user_name: str
    current_plan: str
    total_revenue: float
    lifetime_value: float
    tenure_days: int
    historical_data: List[Dict[str, Any]]
    predictions: Dict[str, Any]
    insights: List[Dict[str, Any]]


@router.get("/overview", response_model=AdminAnalyticsOverviewResponse)
async def get_billing_analytics_overview(
    period_type: str = Query(
        "monthly", regex="^(daily|weekly|monthly|quarterly)$"
    ),
    period_count: int = Query(1, ge=1, le=12),
    end_date: Optional[datetime] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get comprehensive billing analytics overview for admin dashboard.

    - **period_type**: Type of period (daily, weekly, monthly, quarterly)
    - **period_count**: Number of periods to include
    - **end_date**: End date for the analysis (defaults to now)
    """

    service = BillingAnalyticsService(db)

    if end_date is None:
        end_date = datetime.utcnow()

    # Calculate period start based on type and count
    if period_type == "daily":
        period_start = end_date - timedelta(days=period_count)
    elif period_type == "weekly":
        period_start = end_date - timedelta(weeks=period_count)
    elif period_type == "monthly":
        period_start = end_date - timedelta(days=period_count * 30)
    elif period_type == "quarterly":
        period_start = end_date - timedelta(days=period_count * 90)

    overview = service.get_admin_overview(period_start, end_date, period_type)

    return AdminAnalyticsOverviewResponse(
        period_start=period_start,
        period_end=end_date,
        revenue_metrics=RevenueMetricsResponse(**overview["revenue_metrics"]),
        usage_metrics=UsageMetricsResponse(**overview["usage_metrics"]),
        customer_segments=[
            CustomerSegmentResponse(**segment)
            for segment in overview["customer_segments"]
        ],
        top_users=[
            BillingAnalyticsResponse(**user) for user in overview["top_users"]
        ],
        trend_data=[
            TrendDataPoint(**point) for point in overview["trend_data"]
        ],
    )


@router.get("/revenue-trends")
async def get_revenue_trends(
    period_type: str = Query("monthly", regex="^(daily|weekly|monthly)$"),
    months: int = Query(12, ge=1, le=24),
    plan_filter: Optional[str] = Query(None, regex="^(free|pro|enterprise)$"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get revenue trends over time with optional plan filtering.

    - **period_type**: Granularity of the trend data
    - **months**: Number of months to include
    - **plan_filter**: Filter by specific plan type
    """

    service = BillingAnalyticsService(db)
    trends = service.get_revenue_trends(period_type, months, plan_filter)

    return {
        "period_type": period_type,
        "months_included": months,
        "plan_filter": plan_filter,
        "data": trends,
    }


@router.get("/customer-segments")
async def get_customer_segmentation(
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    include_predictions: bool = Query(False),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get customer segmentation analysis with usage patterns and revenue data.

    - **period_start**: Start date for analysis
    - **period_end**: End date for analysis
    - **include_predictions**: Include predictive analytics
    """

    service = BillingAnalyticsService(db)

    if period_end is None:
        period_end = datetime.utcnow()
    if period_start is None:
        period_start = period_end - timedelta(days=90)  # Default to 3 months

    segments = service.get_customer_segmentation(
        period_start, period_end, include_predictions
    )

    return {
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "segments": segments,
    }


@router.get(
    "/users/{user_id}/analytics", response_model=UserAnalyticsDetailResponse
)
async def get_user_analytics_detail(
    user_id: UUID,
    include_predictions: bool = Query(True),
    include_insights: bool = Query(True),
    historical_months: int = Query(12, ge=1, le=24),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get detailed analytics for a specific user including historical data and predictions.

    - **user_id**: UUID of the user to analyze
    - **include_predictions**: Include predictive analytics
    - **include_insights**: Include personalized insights
    - **historical_months**: Number of months of historical data
    """

    service = BillingAnalyticsService(db)

    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    detail = service.get_user_analytics_detail(
        user_id, include_predictions, include_insights, historical_months
    )

    return UserAnalyticsDetailResponse(**detail)


@router.get("/cohort-analysis")
async def get_cohort_analysis(
    cohort_type: str = Query("monthly", regex="^(weekly|monthly|quarterly)$"),
    cohort_size: int = Query(12, ge=3, le=24),
    metric: str = Query("revenue", regex="^(revenue|sessions|retention)$"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get cohort analysis showing user behavior patterns over time.

    - **cohort_type**: Type of cohort grouping
    - **cohort_size**: Number of cohorts to analyze
    - **metric**: Primary metric to analyze
    """

    service = BillingAnalyticsService(db)
    cohort_data = service.get_cohort_analysis(cohort_type, cohort_size, metric)

    return {
        "cohort_type": cohort_type,
        "cohort_size": cohort_size,
        "metric": metric,
        "data": cohort_data,
    }


@router.get("/churn-analysis")
async def get_churn_analysis(
    risk_threshold: float = Query(0.7, ge=0.0, le=1.0),
    period_months: int = Query(6, ge=1, le=12),
    include_predictions: bool = Query(True),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get churn risk analysis with at-risk users and prevention recommendations.

    - **risk_threshold**: Minimum churn risk score to include
    - **period_months**: Number of months to analyze
    - **include_predictions**: Include predictive churn modeling
    """

    service = BillingAnalyticsService(db)

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_months * 30)

    churn_analysis = service.get_churn_analysis(
        start_date, end_date, risk_threshold, include_predictions
    )

    return {
        "analysis_period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "months": period_months,
        },
        "risk_threshold": risk_threshold,
        "summary": churn_analysis["summary"],
        "at_risk_users": churn_analysis["at_risk_users"],
        "recommendations": churn_analysis["recommendations"],
        "predictions": (
            churn_analysis.get("predictions") if include_predictions else None
        ),
    }


@router.get("/plan-performance")
async def get_plan_performance_analysis(
    period_months: int = Query(12, ge=1, le=24),
    include_forecasts: bool = Query(True),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get detailed performance analysis for each subscription plan.

    - **period_months**: Number of months to analyze
    - **include_forecasts**: Include revenue forecasts
    """

    service = BillingAnalyticsService(db)

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_months * 30)

    performance = service.get_plan_performance_analysis(
        start_date, end_date, include_forecasts
    )

    return {
        "analysis_period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "months": period_months,
        },
        "plan_performance": performance["plans"],
        "upgrade_patterns": performance["upgrade_patterns"],
        "forecasts": (
            performance.get("forecasts") if include_forecasts else None
        ),
        "recommendations": performance["recommendations"],
    }


@router.get("/export")
async def export_billing_analytics(
    format: str = Query("csv", regex="^(csv|excel|json)$"),
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    include_user_details: bool = Query(False),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Export billing analytics data in various formats.

    - **format**: Export format (csv, excel, json)
    - **period_start**: Start date for export
    - **period_end**: End date for export
    - **include_user_details**: Include detailed user information
    """

    service = BillingAnalyticsService(db)

    if period_end is None:
        period_end = datetime.utcnow()
    if period_start is None:
        period_start = period_end - timedelta(days=90)

    export_data = service.export_analytics_data(
        format, period_start, period_end, include_user_details
    )

    return export_data


@router.post("/refresh-analytics")
async def refresh_billing_analytics(
    user_id: Optional[UUID] = None,
    period_type: str = Query("monthly", regex="^(daily|monthly)$"),
    force_rebuild: bool = Query(False),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Manually trigger billing analytics refresh for specific user or all users.

    - **user_id**: Specific user to refresh (optional, defaults to all users)
    - **period_type**: Type of analytics to refresh
    - **force_rebuild**: Force complete rebuild of analytics data
    """

    service = BillingAnalyticsService(db)

    try:
        if user_id:
            # Refresh specific user
            result = service.refresh_user_analytics(
                user_id, period_type, force_rebuild
            )
            return {
                "success": True,
                "message": f"Analytics refreshed for user {user_id}",
                "records_updated": result.get("records_updated", 0),
            }
        else:
            # Refresh all users
            result = service.refresh_all_analytics(period_type, force_rebuild)
            return {
                "success": True,
                "message": "Analytics refreshed for all users",
                "users_processed": result.get("users_processed", 0),
                "records_updated": result.get("records_updated", 0),
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh analytics: {str(e)}",
        )


@router.get("/health-score-distribution")
async def get_customer_health_score_distribution(
    current_user: User = Depends(require_staff),  # Staff can view this
    db: Session = Depends(get_db),
):
    """
    Get distribution of customer health scores across the user base.
    """

    service = BillingAnalyticsService(db)
    distribution = service.get_health_score_distribution()

    return {
        "total_users": distribution["total_users"],
        "score_ranges": distribution["score_ranges"],
        "avg_health_score": distribution["avg_health_score"],
        "at_risk_users": distribution["at_risk_users"],
        "power_users": distribution["power_users"],
    }
