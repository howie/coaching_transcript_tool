"""Billing analytics use cases following Clean Architecture principles.

This module provides use cases for billing analytics operations that delegate
to the existing BillingAnalyticsService while maintaining Clean Architecture boundaries.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID

from ...services.billing_analytics_service import BillingAnalyticsService


class BillingAnalyticsOverviewUseCase:
    """Use case for retrieving billing analytics overview."""

    def __init__(self, billing_service: BillingAnalyticsService):
        """Initialize with billing analytics service."""
        self.billing_service = billing_service

    def execute(
        self,
        period_type: str,
        period_count: int,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get comprehensive billing analytics overview."""
        service = self.billing_service

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
        else:
            period_start = end_date - timedelta(days=period_count * 30)

        overview = service.get_admin_overview(period_start, end_date, period_type)

        return {
            "period_start": period_start,
            "period_end": end_date,
            "overview": overview,
        }


class BillingAnalyticsRevenueUseCase:
    """Use case for revenue trends analysis."""

    def __init__(self, billing_service: BillingAnalyticsService):
        """Initialize with billing analytics service."""
        self.billing_service = billing_service

    def execute(
        self,
        period_type: str,
        months: int,
        plan_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get revenue trends over time with optional plan filtering."""
        service = self.billing_service
        trends = service.get_revenue_trends(period_type, months, plan_filter)

        return {
            "period_type": period_type,
            "months_included": months,
            "plan_filter": plan_filter,
            "data": trends,
        }


class BillingAnalyticsSegmentationUseCase:
    """Use case for customer segmentation analysis."""

    def __init__(self, billing_service: BillingAnalyticsService):
        """Initialize with billing analytics service."""
        self.billing_service = billing_service

    def execute(
        self,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        include_predictions: bool = False,
    ) -> Dict[str, Any]:
        """Get customer segmentation analysis."""
        service = self.billing_service

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


class BillingAnalyticsUserDetailUseCase:
    """Use case for detailed user analytics."""

    def __init__(self, billing_service: BillingAnalyticsService):
        """Initialize with billing analytics service."""
        self.billing_service = billing_service

    def execute(
        self,
        user_id: UUID,
        include_predictions: bool = True,
        include_insights: bool = True,
        historical_months: int = 12,
    ) -> Dict[str, Any]:
        """Get detailed analytics for a specific user."""
        service = self.billing_service

        detail = service.get_user_analytics_detail(
            user_id, include_predictions, include_insights, historical_months
        )

        return detail


class BillingAnalyticsCohortUseCase:
    """Use case for cohort analysis."""

    def __init__(self, billing_service: BillingAnalyticsService):
        """Initialize with billing analytics service."""
        self.billing_service = billing_service

    def execute(
        self,
        cohort_type: str,
        cohort_size: int,
        metric: str,
    ) -> Dict[str, Any]:
        """Get cohort analysis showing user behavior patterns."""
        service = self.billing_service
        cohort_data = service.get_cohort_analysis(cohort_type, cohort_size, metric)

        return {
            "cohort_type": cohort_type,
            "cohort_size": cohort_size,
            "metric": metric,
            "data": cohort_data,
        }


class BillingAnalyticsChurnUseCase:
    """Use case for churn analysis."""

    def __init__(self, billing_service: BillingAnalyticsService):
        """Initialize with billing analytics service."""
        self.billing_service = billing_service

    def execute(
        self,
        risk_threshold: float,
        period_months: int,
        include_predictions: bool = True,
    ) -> Dict[str, Any]:
        """Get churn risk analysis with at-risk users."""
        service = self.billing_service

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


class BillingAnalyticsPlanPerformanceUseCase:
    """Use case for plan performance analysis."""

    def __init__(self, billing_service: BillingAnalyticsService):
        """Initialize with billing analytics service."""
        self.billing_service = billing_service

    def execute(
        self,
        period_months: int,
        include_forecasts: bool = True,
    ) -> Dict[str, Any]:
        """Get detailed performance analysis for each subscription plan."""
        service = self.billing_service

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
            "forecasts": (performance.get("forecasts") if include_forecasts else None),
            "recommendations": performance["recommendations"],
        }


class BillingAnalyticsExportUseCase:
    """Use case for exporting billing analytics data."""

    def __init__(self, billing_service: BillingAnalyticsService):
        """Initialize with billing analytics service."""
        self.billing_service = billing_service

    def execute(
        self,
        format: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        include_user_details: bool = False,
    ) -> Dict[str, Any]:
        """Export billing analytics data in various formats."""
        service = self.billing_service

        if period_end is None:
            period_end = datetime.utcnow()
        if period_start is None:
            period_start = period_end - timedelta(days=90)

        export_data = service.export_analytics_data(
            format, period_start, period_end, include_user_details
        )

        return export_data


class BillingAnalyticsRefreshUseCase:
    """Use case for refreshing billing analytics data."""

    def __init__(self, billing_service: BillingAnalyticsService):
        """Initialize with billing analytics service."""
        self.billing_service = billing_service

    def execute(
        self,
        user_id: Optional[UUID] = None,
        period_type: str = "monthly",
        force_rebuild: bool = False,
    ) -> Dict[str, Any]:
        """Manually trigger billing analytics refresh."""
        service = self.billing_service

        if user_id:
            # Refresh specific user
            result = service.refresh_user_analytics(user_id, period_type, force_rebuild)
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


class BillingAnalyticsHealthScoreUseCase:
    """Use case for customer health score distribution."""

    def __init__(self, billing_service: BillingAnalyticsService):
        """Initialize with billing analytics service."""
        self.billing_service = billing_service

    def execute(self) -> Dict[str, Any]:
        """Get distribution of customer health scores."""
        service = self.billing_service
        distribution = service.get_health_score_distribution()

        return {
            "total_users": distribution["total_users"],
            "score_ranges": distribution["score_ranges"],
            "avg_health_score": distribution["avg_health_score"],
            "at_risk_users": distribution["at_risk_users"],
            "power_users": distribution["power_users"],
        }
