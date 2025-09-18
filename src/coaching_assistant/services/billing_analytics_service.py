"""Billing Analytics Service for enhanced admin reporting and revenue analysis."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID
import csv
from io import StringIO

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from ..models.billing_analytics import BillingAnalytics
from ..models.user import User
from ..models.usage_history import UsageHistory
from ..services.usage_analytics_service import UsageAnalyticsService

logger = logging.getLogger(__name__)


class BillingAnalyticsService:
    """Service for enhanced billing analytics and admin reporting."""

    def __init__(self, db: Session):
        self.db = db
        self.usage_analytics_service = UsageAnalyticsService(db)

    def get_admin_overview(
        self,
        period_start: datetime,
        period_end: datetime,
        period_type: str = "monthly",
    ) -> Dict[str, Any]:
        """Get comprehensive admin analytics overview."""
        logger.info(
            f"📊 Getting admin overview from {period_start} to {period_end}"
        )

        # Get billing analytics for the period
        billing_data = (
            self.db.query(BillingAnalytics)
            .filter(
                and_(
                    BillingAnalytics.period_start >= period_start,
                    BillingAnalytics.period_end <= period_end,
                    BillingAnalytics.period_type == period_type,
                )
            )
            .all()
        )

        # Calculate revenue metrics
        revenue_metrics = self._calculate_revenue_metrics(billing_data)

        # Calculate usage metrics
        usage_metrics = self._calculate_usage_metrics(billing_data)

        # Get customer segmentation
        customer_segments = self._get_customer_segments(billing_data)

        # Get top users by revenue
        top_users = self._get_top_users(billing_data, limit=10)

        # Get trend data
        trend_data = self._get_trend_data(
            period_start, period_end, period_type
        )

        return {
            "revenue_metrics": revenue_metrics,
            "usage_metrics": usage_metrics,
            "customer_segments": customer_segments,
            "top_users": top_users,
            "trend_data": trend_data,
        }

    def get_revenue_trends(
        self, period_type: str, months: int, plan_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get revenue trends over time with optional plan filtering."""
        logger.info(
            f"📈 Getting revenue trends for {months} months, period: {period_type}"
        )

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=months * 30)

        query = self.db.query(BillingAnalytics).filter(
            and_(
                BillingAnalytics.period_start >= start_date,
                BillingAnalytics.period_type == period_type,
            )
        )

        if plan_filter:
            query = query.filter(
                BillingAnalytics.plan_name == plan_filter.upper()
            )

        billing_data = query.order_by(BillingAnalytics.period_start).all()

        # Group by period and calculate trends
        trends = {}
        for record in billing_data:
            period_key = record.period_start.strftime("%Y-%m-%d")
            if period_key not in trends:
                trends[period_key] = {
                    "date": period_key,
                    "revenue": 0,
                    "users": 0,
                    "sessions": 0,
                    "minutes": 0,
                }

            trends[period_key]["revenue"] += float(record.total_revenue_usd)
            trends[period_key]["users"] += 1
            trends[period_key]["sessions"] += record.sessions_created
            trends[period_key]["minutes"] += float(
                record.total_minutes_processed
            )

        return list(trends.values())

    def get_customer_segmentation(
        self,
        period_start: datetime,
        period_end: datetime,
        include_predictions: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get customer segmentation analysis."""
        logger.info(f"👥 Getting customer segmentation analysis")

        billing_data = (
            self.db.query(BillingAnalytics)
            .filter(
                and_(
                    BillingAnalytics.period_start >= period_start,
                    BillingAnalytics.period_end <= period_end,
                )
            )
            .all()
        )

        segments = self._analyze_customer_segments(billing_data)

        if include_predictions:
            # Add predictive insights to segments
            for segment in segments:
                segment["predictions"] = self._get_segment_predictions(
                    segment["segment"]
                )

        return segments

    def get_user_analytics_detail(
        self,
        user_id: UUID,
        include_predictions: bool = True,
        include_insights: bool = True,
        historical_months: int = 12,
    ) -> Dict[str, Any]:
        """Get detailed analytics for a specific user."""
        logger.info(f"🔍 Getting detailed analytics for user {user_id}")

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Get historical billing data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=historical_months * 30)

        historical_data = (
            self.db.query(BillingAnalytics)
            .filter(
                and_(
                    BillingAnalytics.user_id == user_id,
                    BillingAnalytics.period_start >= start_date,
                )
            )
            .order_by(BillingAnalytics.period_start)
            .all()
        )

        # Calculate metrics
        total_revenue = sum(
            float(record.total_revenue_usd) for record in historical_data
        )
        tenure_days = (
            (datetime.utcnow() - user.created_at).days
            if user.created_at
            else 0
        )

        detail = {
            "user_id": user_id,
            "user_email": user.email,
            "user_name": user.name,
            "current_plan": user.plan.value,
            "total_revenue": total_revenue,
            "lifetime_value": self._calculate_lifetime_value(user_id),
            "tenure_days": tenure_days,
            "historical_data": [
                record.to_dict() for record in historical_data
            ],
        }

        if include_predictions:
            detail["predictions"] = self.usage_analytics_service.predict_usage(
                user_id
            )

        if include_insights:
            detail["insights"] = (
                self.usage_analytics_service.generate_insights(user_id)
            )

        return detail

    def get_cohort_analysis(
        self, cohort_type: str, cohort_size: int, metric: str
    ) -> Dict[str, Any]:
        """Get cohort analysis showing user behavior patterns."""
        logger.info(
            f"📊 Getting cohort analysis: {cohort_type}, size: {cohort_size}, metric: {metric}"
        )

        # This is a simplified implementation - would need more complex logic for production
        cohorts = {}

        # Get users grouped by signup period
        if cohort_type == "monthly":
            date_trunc = func.date_trunc("month", User.created_at)
        elif cohort_type == "weekly":
            date_trunc = func.date_trunc("week", User.created_at)
        else:
            date_trunc = func.date_trunc("quarter", User.created_at)

        cohort_users = (
            self.db.query(
                date_trunc.label("cohort_period"),
                func.count(User.id).label("user_count"),
            )
            .group_by(date_trunc)
            .order_by(date_trunc.desc())
            .limit(cohort_size)
            .all()
        )

        # For each cohort, calculate the specified metric over time
        cohort_data = []
        for cohort in cohort_users:
            cohort_data.append(
                {
                    "cohort_period": cohort.cohort_period.strftime("%Y-%m"),
                    "initial_users": cohort.user_count,
                    "metric_data": self._get_cohort_metric_data(
                        cohort.cohort_period, metric
                    ),
                }
            )

        return {
            "cohort_type": cohort_type,
            "metric": metric,
            "cohorts": cohort_data,
        }

    def get_churn_analysis(
        self,
        start_date: datetime,
        end_date: datetime,
        risk_threshold: float = 0.7,
        include_predictions: bool = True,
    ) -> Dict[str, Any]:
        """Get churn risk analysis with at-risk users."""
        logger.info(
            f"⚠️ Getting churn analysis from {start_date} to {end_date}"
        )

        # Get users with high churn risk scores
        at_risk_users = (
            self.db.query(BillingAnalytics)
            .filter(
                and_(
                    BillingAnalytics.churn_risk_score >= risk_threshold,
                    BillingAnalytics.period_start >= start_date,
                    BillingAnalytics.period_end <= end_date,
                )
            )
            .order_by(desc(BillingAnalytics.churn_risk_score))
            .all()
        )

        # Group at-risk users by risk level
        high_risk = [
            u for u in at_risk_users if float(u.churn_risk_score) >= 0.9
        ]
        medium_risk = [
            u for u in at_risk_users if 0.7 <= float(u.churn_risk_score) < 0.9
        ]

        summary = {
            "total_at_risk": len(at_risk_users),
            "high_risk_count": len(high_risk),
            "medium_risk_count": len(medium_risk),
            "potential_revenue_at_risk": sum(
                float(u.total_revenue_usd) for u in at_risk_users
            ),
        }

        # Generate recommendations
        recommendations = self._generate_churn_prevention_recommendations(
            at_risk_users
        )

        analysis = {
            "summary": summary,
            "at_risk_users": [
                self._format_churn_user(user) for user in at_risk_users[:50]
            ],
            "recommendations": recommendations,
        }

        if include_predictions:
            analysis["predictions"] = self._get_churn_predictions(
                at_risk_users
            )

        return analysis

    def get_plan_performance_analysis(
        self,
        start_date: datetime,
        end_date: datetime,
        include_forecasts: bool = True,
    ) -> Dict[str, Any]:
        """Get detailed performance analysis for each subscription plan."""
        logger.info(f"📋 Getting plan performance analysis")

        plan_performance = {}

        for plan in ["FREE", "PRO", "ENTERPRISE"]:
            plan_data = (
                self.db.query(BillingAnalytics)
                .filter(
                    and_(
                        BillingAnalytics.plan_name == plan,
                        BillingAnalytics.period_start >= start_date,
                        BillingAnalytics.period_end <= end_date,
                    )
                )
                .all()
            )

            if plan_data:
                plan_performance[plan] = {
                    "user_count": len(
                        set(record.user_id for record in plan_data)
                    ),
                    "total_revenue": sum(
                        float(record.total_revenue_usd) for record in plan_data
                    ),
                    "avg_utilization": sum(
                        float(record.plan_utilization_percentage)
                        for record in plan_data
                    )
                    / len(plan_data),
                    "avg_health_score": sum(
                        record.calculate_customer_health_score()
                        for record in plan_data
                    )
                    / len(plan_data),
                    "churn_risk_users": len(
                        [
                            r
                            for r in plan_data
                            if float(r.churn_risk_score) > 0.7
                        ]
                    ),
                }

        # Get upgrade patterns
        upgrade_patterns = self._analyze_upgrade_patterns(start_date, end_date)

        analysis = {
            "plans": plan_performance,
            "upgrade_patterns": upgrade_patterns,
            "recommendations": self._generate_plan_recommendations(
                plan_performance
            ),
        }

        if include_forecasts:
            analysis["forecasts"] = self._generate_plan_forecasts(
                plan_performance
            )

        return analysis

    def export_analytics_data(
        self,
        format: str,
        period_start: datetime,
        period_end: datetime,
        include_user_details: bool = False,
    ) -> Dict[str, Any]:
        """Export billing analytics data in various formats."""
        logger.info(f"📤 Exporting analytics data in {format} format")

        # Get billing data for the period
        billing_data = (
            self.db.query(BillingAnalytics)
            .filter(
                and_(
                    BillingAnalytics.period_start >= period_start,
                    BillingAnalytics.period_end <= period_end,
                )
            )
            .all()
        )

        if include_user_details:
            # Join with user data
            export_data = []
            for record in billing_data:
                user = (
                    self.db.query(User)
                    .filter(User.id == record.user_id)
                    .first()
                )
                data = record.to_dict()
                if user:
                    data.update(
                        {
                            "user_email": user.email,
                            "user_name": user.name,
                            "user_signup_date": (
                                user.created_at.isoformat()
                                if user.created_at
                                else None
                            ),
                        }
                    )
                export_data.append(data)
        else:
            export_data = [record.to_dict() for record in billing_data]

        if format == "csv":
            return self._export_to_csv(export_data)
        elif format == "excel":
            return self._export_to_excel(export_data)
        else:  # json
            return {
                "format": "json",
                "data": export_data,
                "total_records": len(export_data),
            }

    def refresh_user_analytics(
        self,
        user_id: UUID,
        period_type: str = "monthly",
        force_rebuild: bool = False,
    ) -> Dict[str, Any]:
        """Manually refresh analytics for a specific user."""
        logger.info(f"🔄 Refreshing analytics for user {user_id}")

        # Get current month's data
        now = datetime.utcnow()
        if period_type == "monthly":
            period_start = now.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            if period_start.month == 12:
                period_end = period_start.replace(
                    year=period_start.year + 1, month=1
                )
            else:
                period_end = period_start.replace(month=period_start.month + 1)
        else:  # daily
            period_start = now.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            period_end = period_start + timedelta(days=1)

        # Check if record exists
        existing = (
            self.db.query(BillingAnalytics)
            .filter(
                and_(
                    BillingAnalytics.user_id == user_id,
                    BillingAnalytics.period_type == period_type,
                    BillingAnalytics.period_start == period_start,
                )
            )
            .first()
        )

        if existing and not force_rebuild:
            # Update existing record
            updated_data = self._calculate_user_billing_data(
                user_id, period_start, period_end
            )
            for key, value in updated_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.recorded_at = datetime.utcnow()
            self.db.commit()
            return {"records_updated": 1}
        else:
            # Create new record or rebuild
            if existing and force_rebuild:
                self.db.delete(existing)

            billing_data = self._calculate_user_billing_data(
                user_id, period_start, period_end
            )
            new_record = BillingAnalytics.create_from_usage_data(
                user_id=user_id,
                period_type=period_type,
                period_start=period_start,
                period_end=period_end,
                usage_data=billing_data,
            )
            self.db.add(new_record)
            self.db.commit()
            return {"records_updated": 1}

    def refresh_all_analytics(
        self, period_type: str = "monthly", force_rebuild: bool = False
    ) -> Dict[str, Any]:
        """Refresh analytics for all users."""
        logger.info(f"🔄 Refreshing analytics for all users")

        users = self.db.query(User).all()
        records_updated = 0

        for user in users:
            try:
                result = self.refresh_user_analytics(
                    user.id, period_type, force_rebuild
                )
                records_updated += result.get("records_updated", 0)
            except Exception as e:
                logger.error(
                    f"Failed to refresh analytics for user {user.id}: {e}"
                )

        return {
            "users_processed": len(users),
            "records_updated": records_updated,
        }

    def get_health_score_distribution(self) -> Dict[str, Any]:
        """Get distribution of customer health scores."""
        logger.info(f"📊 Getting health score distribution")

        # Get recent billing analytics
        recent_data = (
            self.db.query(BillingAnalytics)
            .filter(
                BillingAnalytics.period_start
                >= datetime.utcnow() - timedelta(days=60)
            )
            .all()
        )

        if not recent_data:
            return {
                "total_users": 0,
                "score_ranges": {},
                "avg_health_score": 0,
                "at_risk_users": 0,
                "power_users": 0,
            }

        health_scores = [
            record.calculate_customer_health_score() for record in recent_data
        ]

        # Categorize scores
        score_ranges = {
            "excellent (90-100)": len([s for s in health_scores if s >= 90]),
            "good (70-89)": len([s for s in health_scores if 70 <= s < 90]),
            "average (50-69)": len([s for s in health_scores if 50 <= s < 70]),
            "poor (30-49)": len([s for s in health_scores if 30 <= s < 50]),
            "critical (0-29)": len([s for s in health_scores if s < 30]),
        }

        return {
            "total_users": len(recent_data),
            "score_ranges": score_ranges,
            "avg_health_score": sum(health_scores) / len(health_scores),
            "at_risk_users": len([r for r in recent_data if r.is_at_risk]),
            "power_users": len([r for r in recent_data if r.is_power_user]),
        }

    # Helper methods

    def _calculate_revenue_metrics(
        self, billing_data: List[BillingAnalytics]
    ) -> Dict[str, float]:
        """Calculate aggregate revenue metrics."""
        if not billing_data:
            return {
                "total_revenue": 0,
                "subscription_revenue": 0,
                "overage_revenue": 0,
                "one_time_fees": 0,
                "gross_margin": 0,
                "gross_margin_percentage": 0,
                "avg_revenue_per_user": 0,
                "avg_revenue_per_minute": 0,
            }

        total_revenue = sum(
            float(record.total_revenue_usd) for record in billing_data
        )
        total_cost = sum(
            float(record.total_provider_cost_usd) for record in billing_data
        )
        total_minutes = sum(
            float(record.total_minutes_processed) for record in billing_data
        )

        return {
            "total_revenue": total_revenue,
            "subscription_revenue": sum(
                float(record.subscription_revenue_usd)
                for record in billing_data
            ),
            "overage_revenue": sum(
                float(record.usage_overage_usd) for record in billing_data
            ),
            "one_time_fees": sum(
                float(record.one_time_fees_usd) for record in billing_data
            ),
            "gross_margin": total_revenue - total_cost,
            "gross_margin_percentage": (
                ((total_revenue - total_cost) / total_revenue * 100)
                if total_revenue > 0
                else 0
            ),
            "avg_revenue_per_user": total_revenue / len(billing_data),
            "avg_revenue_per_minute": (
                total_revenue / total_minutes if total_minutes > 0 else 0
            ),
        }

    def _calculate_usage_metrics(
        self, billing_data: List[BillingAnalytics]
    ) -> Dict[str, Any]:
        """Calculate aggregate usage metrics."""
        if not billing_data:
            return {
                "total_sessions": 0,
                "total_transcriptions": 0,
                "total_minutes": 0,
                "total_hours": 0,
                "avg_session_duration": 0,
                "success_rate": 0,
                "unique_active_users": 0,
            }

        total_sessions = sum(
            record.sessions_created for record in billing_data
        )
        total_transcriptions = sum(
            record.transcriptions_completed for record in billing_data
        )
        total_minutes = sum(
            float(record.total_minutes_processed) for record in billing_data
        )
        success_rates = [
            float(record.success_rate_percentage)
            for record in billing_data
            if record.success_rate_percentage
        ]

        return {
            "total_sessions": total_sessions,
            "total_transcriptions": total_transcriptions,
            "total_minutes": total_minutes,
            "total_hours": total_minutes / 60,
            "avg_session_duration": (
                total_minutes / total_transcriptions
                if total_transcriptions > 0
                else 0
            ),
            "success_rate": (
                sum(success_rates) / len(success_rates) if success_rates else 0
            ),
            "unique_active_users": len(
                set(record.user_id for record in billing_data)
            ),
        }

    def _get_customer_segments(
        self, billing_data: List[BillingAnalytics]
    ) -> List[Dict[str, Any]]:
        """Get customer segmentation data."""
        segments = {}

        for record in billing_data:
            segment = record.user_segment or "unknown"
            if segment not in segments:
                segments[segment] = {
                    "segment": segment,
                    "user_count": 0,
                    "total_revenue": 0,
                    "total_utilization": 0,
                    "churn_risk_users": 0,
                }

            segments[segment]["user_count"] += 1
            segments[segment]["total_revenue"] += float(
                record.total_revenue_usd
            )
            segments[segment]["total_utilization"] += float(
                record.plan_utilization_percentage
            )
            if float(record.churn_risk_score) > 0.7:
                segments[segment]["churn_risk_users"] += 1

        # Calculate averages
        for segment_data in segments.values():
            if segment_data["user_count"] > 0:
                segment_data["avg_revenue_per_user"] = (
                    segment_data["total_revenue"] / segment_data["user_count"]
                )
                segment_data["avg_utilization"] = (
                    segment_data["total_utilization"]
                    / segment_data["user_count"]
                )

        return list(segments.values())

    def _get_top_users(
        self, billing_data: List[BillingAnalytics], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top users by revenue."""
        # Sort by revenue and get top users
        sorted_data = sorted(
            billing_data,
            key=lambda x: float(x.total_revenue_usd),
            reverse=True,
        )

        top_users = []
        for record in sorted_data[:limit]:
            user = (
                self.db.query(User).filter(User.id == record.user_id).first()
            )
            if user:
                top_users.append(
                    {
                        "id": record.id,
                        "user_id": record.user_id,
                        "user_email": user.email,
                        "user_name": user.name,
                        "period_type": record.period_type,
                        "period_start": record.period_start,
                        "period_end": record.period_end,
                        "plan_name": record.plan_name,
                        "total_revenue_usd": float(record.total_revenue_usd),
                        "total_minutes_processed": float(
                            record.total_minutes_processed
                        ),
                        "plan_utilization_percentage": float(
                            record.plan_utilization_percentage
                        ),
                        "churn_risk_score": float(record.churn_risk_score),
                        "customer_health_score": record.calculate_customer_health_score(),
                        "is_power_user": record.is_power_user,
                        "is_at_risk": record.is_at_risk,
                    }
                )

        return top_users

    def _get_trend_data(
        self, period_start: datetime, period_end: datetime, period_type: str
    ) -> List[Dict[str, Any]]:
        """Get trend data points for the specified period."""
        # This is a simplified implementation
        # In production, you'd want more sophisticated trend analysis

        trends = []
        current_date = period_start

        while current_date < period_end:
            # Get data for this specific period
            if period_type == "daily":
                next_date = current_date + timedelta(days=1)
            elif period_type == "weekly":
                next_date = current_date + timedelta(weeks=1)
            else:  # monthly
                if current_date.month == 12:
                    next_date = current_date.replace(
                        year=current_date.year + 1, month=1
                    )
                else:
                    next_date = current_date.replace(
                        month=current_date.month + 1
                    )

            period_data = (
                self.db.query(BillingAnalytics)
                .filter(
                    and_(
                        BillingAnalytics.period_start >= current_date,
                        BillingAnalytics.period_start < next_date,
                    )
                )
                .all()
            )

            trends.append(
                {
                    "date": current_date.strftime("%Y-%m-%d"),
                    "revenue": sum(
                        float(record.total_revenue_usd)
                        for record in period_data
                    ),
                    "users": len(
                        set(record.user_id for record in period_data)
                    ),
                    "sessions": sum(
                        record.sessions_created for record in period_data
                    ),
                    "minutes": sum(
                        float(record.total_minutes_processed)
                        for record in period_data
                    ),
                    "new_signups": self._calculate_new_signups(
                        current_date, next_date
                    ),
                    "churned_users": self._calculate_churned_users(
                        current_date, next_date
                    )
                }
            )

            current_date = next_date

        return trends

    def _calculate_user_billing_data(
        self, user_id: UUID, period_start: datetime, period_end: datetime
    ) -> Dict[str, Any]:
        """Calculate billing data for a specific user and period."""
        # Use existing usage analytics service to get usage data
        usage_data = self.usage_analytics_service._aggregate_usage_data(
            user_id, period_start, period_end
        )

        # Add billing-specific calculations
        user = self.db.query(User).filter(User.id == user_id).first()

        # Calculate revenue from usage data and user plan
        revenue_data = self._calculate_revenue_data(
            user, usage_data, period_start, period_end
        )

        # User profile data
        user_profile = {
            "signup_date": user.created_at,
            "tenure_days": (
                (datetime.utcnow() - user.created_at).days
                if user.created_at
                else 0
            ),
            "segment": self._determine_user_segment(user_id),
            "timezone": self._get_user_timezone(user),
            "country": self._get_user_country(user),
            "language": user.get_preferences().get("language", "en"),
        }

        # Merge all data
        billing_data = {**usage_data, **revenue_data, **user_profile}

        return billing_data

    def _calculate_new_signups(self, start_date: datetime, end_date: datetime) -> int:
        """Calculate actual new signups for the period."""
        new_users = (
            self.db.query(User)
            .filter(
                and_(
                    User.created_at >= start_date,
                    User.created_at < end_date,
                )
            )
            .count()
        )
        return new_users

    def _calculate_churned_users(self, start_date: datetime, end_date: datetime) -> int:
        """Calculate actual churned users for the period."""
        # Define churn as users who had activity before this period but none during
        # This is a simplified implementation - in practice, you'd want more
        # sophisticated churn detection

        # Users who were active before the period
        active_before = (
            self.db.query(User.id)
            .join(UsageHistory)
            .filter(UsageHistory.period_end < start_date)
            .distinct()
            .subquery()
        )

        # Users who were active during the period
        active_during = (
            self.db.query(User.id)
            .join(UsageHistory)
            .filter(
                and_(
                    UsageHistory.period_start >= start_date,
                    UsageHistory.period_end < end_date,
                )
            )
            .distinct()
            .subquery()
        )

        # Churned users = active before but not active during
        churned_count = (
            self.db.query(User)
            .filter(
                and_(
                    User.id.in_(self.db.query(active_before.c.id)),
                    ~User.id.in_(self.db.query(active_during.c.id))
                )
            )
            .count()
        )

        return churned_count

    def _calculate_revenue_data(
        self, user, usage_data, period_start: datetime, period_end: datetime
    ) -> Dict[str, Any]:
        """Calculate revenue data based on user plan and usage."""
        from ..services.plan_limits import PlanLimitsService

        plan_service = PlanLimitsService()
        plan_config = plan_service.get_plan_limit(user.plan.value)

        # Calculate subscription revenue based on plan
        days_in_period = (period_end - period_start).days
        monthly_price = getattr(plan_config, 'monthly_price_usd', 0) or 0

        # Pro-rate for the period
        subscription_revenue = (monthly_price * days_in_period) / 30

        # Calculate overage revenue (simplified)
        overage_revenue = 0
        transcriptions_used = usage_data.get('transcriptions_completed', 0)
        if transcriptions_used > plan_config.max_transcriptions:
            overage_count = transcriptions_used - plan_config.max_transcriptions
            overage_revenue = overage_count * 0.10  # $0.10 per overage

        total_revenue = subscription_revenue + overage_revenue

        return {
            "total_revenue": round(total_revenue, 2),
            "subscription_revenue": round(subscription_revenue, 2),
            "overage_revenue": round(overage_revenue, 2),
            "one_time_fees": 0,
        }

    def _get_user_timezone(self, user) -> str:
        """Get user timezone from preferences or default."""
        try:
            preferences = user.get_preferences()
            return preferences.get("timezone", "UTC")
        except (AttributeError, TypeError):
            return "UTC"

    def _get_user_country(self, user) -> str:
        """Get user country from profile or default."""
        try:
            preferences = user.get_preferences()
            return preferences.get("country", "Unknown")
        except (AttributeError, TypeError):
            return "Unknown"

    def _determine_user_segment(self, user_id: UUID) -> str:
        """Determine user segment based on usage patterns."""
        # Simplified segmentation logic
        recent_usage = (
            self.db.query(UsageHistory)
            .filter(
                and_(
                    UsageHistory.user_id == user_id,
                    UsageHistory.period_start
                    >= datetime.utcnow() - timedelta(days=90),
                )
            )
            .all()
        )

        if not recent_usage:
            return "new"

        avg_minutes = sum(
            float(record.audio_minutes_processed) for record in recent_usage
        ) / len(recent_usage)
        avg_utilization = sum(
            record.utilization_percentage for record in recent_usage
        ) / len(recent_usage)

        if avg_utilization > 80 and avg_minutes > 300:
            return "power"
        elif avg_utilization > 50:
            return "growing"
        else:
            return "casual"

    def _export_to_csv(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Export data to CSV format."""
        if not data:
            return {"format": "csv", "data": "", "total_records": 0}

        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

        return {
            "format": "csv",
            "data": output.getvalue(),
            "total_records": len(data),
        }

    def _export_to_excel(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Export data to Excel format (simplified)."""
        # This would require openpyxl or similar library
        # For now, return CSV format as fallback
        return self._export_to_csv(data)

    # Additional helper methods for cohort analysis, churn predictions, etc.
    # These would be more complex in production

    def _get_cohort_metric_data(
        self, cohort_period: datetime, metric: str
    ) -> List[Dict[str, Any]]:
        """Get metric data for a specific cohort over time."""
        # Simplified implementation
        return [
            {"period": "month_1", "value": 100},
            {"period": "month_2", "value": 85},
        ]

    def _analyze_customer_segments(
        self, billing_data: List[BillingAnalytics]
    ) -> List[Dict[str, Any]]:
        """Analyze and return customer segments."""
        return self._get_customer_segments(billing_data)

    def _get_segment_predictions(self, segment: str) -> Dict[str, Any]:
        """Get predictions for a specific customer segment."""
        return {"growth_rate": 10, "churn_likelihood": 0.1}

    def _calculate_lifetime_value(self, user_id: UUID) -> float:
        """Calculate estimated lifetime value for a user."""
        # Simplified LTV calculation
        historical_revenue = (
            self.db.query(func.sum(BillingAnalytics.total_revenue_usd))
            .filter(BillingAnalytics.user_id == user_id)
            .scalar()
            or 0
        )

        return float(historical_revenue) * 1.5  # Simple multiplier

    def _format_churn_user(self, record: BillingAnalytics) -> Dict[str, Any]:
        """Format churn risk user data."""
        user = self.db.query(User).filter(User.id == record.user_id).first()
        return {
            "user_id": record.user_id,
            "email": user.email if user else "Unknown",
            "plan": record.plan_name,
            "churn_risk_score": float(record.churn_risk_score),
            "revenue": float(record.total_revenue_usd),
            "utilization": float(record.plan_utilization_percentage),
        }

    def _generate_churn_prevention_recommendations(
        self, at_risk_users: List[BillingAnalytics]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for churn prevention."""
        return [
            {
                "type": "engagement",
                "title": "Increase User Engagement",
                "description": "Reach out to users with low utilization rates",
                "priority": "high",
            },
            {
                "type": "support",
                "title": "Proactive Support",
                "description": "Offer help to users showing declining usage patterns",
                "priority": "medium",
            },
        ]

    def _get_churn_predictions(
        self, at_risk_users: List[BillingAnalytics]
    ) -> Dict[str, Any]:
        """Get churn predictions for at-risk users."""
        return {
            "predicted_churn_30_days": len(at_risk_users) * 0.3,
            "predicted_revenue_loss": sum(
                float(u.total_revenue_usd) for u in at_risk_users
            )
            * 0.3,
        }

    def _analyze_upgrade_patterns(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Analyze plan upgrade patterns."""
        # This would analyze users who changed plans during the period
        return {"free_to_pro": 10, "pro_to_enterprise": 3, "downgrades": 2}

    def _generate_plan_recommendations(
        self, plan_performance: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on plan performance."""
        return [
            {
                "recommendation": "Focus on converting FREE users to PRO",
                "reason": "High utilization in FREE tier indicates upgrade potential",
            }
        ]

    def _generate_plan_forecasts(
        self, plan_performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate revenue forecasts for each plan."""
        return {
            "FREE": {"forecasted_revenue": 0, "growth_rate": 5},
            "PRO": {"forecasted_revenue": 10000, "growth_rate": 15},
            "ENTERPRISE": {"forecasted_revenue": 50000, "growth_rate": 25},
        }
