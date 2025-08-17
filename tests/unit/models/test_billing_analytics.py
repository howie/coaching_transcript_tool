"""Tests for BillingAnalytics model."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from coaching_assistant.models.billing_analytics import BillingAnalytics


class TestBillingAnalytics:
    """Test BillingAnalytics model functionality."""
    
    def test_billing_analytics_creation(self):
        """Test creating a BillingAnalytics record."""
        user_id = uuid4()
        period_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(days=30)
        
        billing_analytics = BillingAnalytics(
            user_id=user_id,
            period_type="monthly",
            period_start=period_start,
            period_end=period_end,
            plan_name="PRO",
            total_revenue_usd=Decimal("99.99"),
            total_minutes_processed=Decimal("500.0"),
            plan_utilization_percentage=Decimal("75.5"),
            churn_risk_score=Decimal("0.2")
        )
        
        assert billing_analytics.user_id == user_id
        assert billing_analytics.period_type == "monthly"
        assert billing_analytics.plan_name == "PRO"
        assert billing_analytics.total_revenue_usd == Decimal("99.99")
        assert billing_analytics.total_minutes_processed == Decimal("500.0")
        assert billing_analytics.plan_utilization_percentage == Decimal("75.5")
        assert billing_analytics.churn_risk_score == Decimal("0.2")
    
    def test_total_hours_processed_property(self):
        """Test total_hours_processed property calculation."""
        billing_analytics = BillingAnalytics(
            total_minutes_processed=Decimal("120.0")
        )
        
        assert billing_analytics.total_hours_processed == 2.0
    
    def test_gross_margin_calculation(self):
        """Test gross margin calculations."""
        billing_analytics = BillingAnalytics(
            total_revenue_usd=Decimal("100.00"),
            total_provider_cost_usd=Decimal("25.00")
        )
        
        assert billing_analytics.gross_margin_usd == 75.0
        assert billing_analytics.gross_margin_percentage == 75.0
    
    def test_gross_margin_zero_revenue(self):
        """Test gross margin with zero revenue."""
        billing_analytics = BillingAnalytics(
            total_revenue_usd=Decimal("0.00"),
            total_provider_cost_usd=Decimal("10.00")
        )
        
        assert billing_analytics.gross_margin_usd == -10.0
        assert billing_analytics.gross_margin_percentage == 0.0
    
    def test_revenue_per_minute(self):
        """Test revenue per minute calculation."""
        billing_analytics = BillingAnalytics(
            total_revenue_usd=Decimal("50.00"),
            total_minutes_processed=Decimal("100.0")
        )
        
        assert billing_analytics.revenue_per_minute == 0.5
    
    def test_revenue_per_minute_zero_minutes(self):
        """Test revenue per minute with zero minutes."""
        billing_analytics = BillingAnalytics(
            total_revenue_usd=Decimal("50.00"),
            total_minutes_processed=Decimal("0.0")
        )
        
        assert billing_analytics.revenue_per_minute == 0.0
    
    def test_cost_per_minute(self):
        """Test cost per minute calculation."""
        billing_analytics = BillingAnalytics(
            total_provider_cost_usd=Decimal("20.00"),
            total_minutes_processed=Decimal("100.0")
        )
        
        assert billing_analytics.cost_per_minute == 0.2
    
    def test_avg_session_duration_minutes(self):
        """Test average session duration calculation."""
        billing_analytics = BillingAnalytics(
            total_minutes_processed=Decimal("300.0"),
            transcriptions_completed=10
        )
        
        assert billing_analytics.avg_session_duration_minutes == 30.0
    
    def test_avg_session_duration_zero_transcriptions(self):
        """Test average session duration with zero transcriptions."""
        billing_analytics = BillingAnalytics(
            total_minutes_processed=Decimal("300.0"),
            transcriptions_completed=0
        )
        
        assert billing_analytics.avg_session_duration_minutes == 0.0
    
    def test_is_power_user_true(self):
        """Test is_power_user property when conditions are met."""
        period_start = datetime.utcnow()
        period_end = period_start + timedelta(days=30)
        
        billing_analytics = BillingAnalytics(
            period_start=period_start,
            period_end=period_end,
            plan_utilization_percentage=Decimal("80.0"),
            days_active_in_period=20,  # More than 60% of 30 days
            avg_sessions_per_active_day=Decimal("4.0")
        )
        
        assert billing_analytics.is_power_user is True
    
    def test_is_power_user_false(self):
        """Test is_power_user property when conditions are not met."""
        period_start = datetime.utcnow()
        period_end = period_start + timedelta(days=30)
        
        billing_analytics = BillingAnalytics(
            period_start=period_start,
            period_end=period_end,
            plan_utilization_percentage=Decimal("50.0"),  # Below 70%
            days_active_in_period=10,  # Less than 60% of 30 days
            avg_sessions_per_active_day=Decimal("2.0")
        )
        
        assert billing_analytics.is_power_user is False
    
    def test_is_at_risk_high_churn_score(self):
        """Test is_at_risk property with high churn score."""
        period_start = datetime.utcnow()
        period_end = period_start + timedelta(days=30)
        
        billing_analytics = BillingAnalytics(
            period_start=period_start,
            period_end=period_end,
            churn_risk_score=Decimal("0.8"),  # Above 0.7
            days_active_in_period=25,
            plan_utilization_percentage=Decimal("50.0")
        )
        
        assert billing_analytics.is_at_risk is True
    
    def test_is_at_risk_low_activity(self):
        """Test is_at_risk property with low activity."""
        period_start = datetime.utcnow()
        period_end = period_start + timedelta(days=30)
        
        billing_analytics = BillingAnalytics(
            period_start=period_start,
            period_end=period_end,
            churn_risk_score=Decimal("0.3"),
            days_active_in_period=5,  # Less than 20% of 30 days
            plan_utilization_percentage=Decimal("50.0")
        )
        
        assert billing_analytics.is_at_risk is True
    
    def test_is_at_risk_low_utilization(self):
        """Test is_at_risk property with low utilization."""
        period_start = datetime.utcnow()
        period_end = period_start + timedelta(days=30)
        
        billing_analytics = BillingAnalytics(
            period_start=period_start,
            period_end=period_end,
            churn_risk_score=Decimal("0.3"),
            days_active_in_period=20,
            plan_utilization_percentage=Decimal("5.0")  # Below 10%
        )
        
        assert billing_analytics.is_at_risk is True
    
    def test_is_at_risk_false(self):
        """Test is_at_risk property when user is not at risk."""
        period_start = datetime.utcnow()
        period_end = period_start + timedelta(days=30)
        
        billing_analytics = BillingAnalytics(
            period_start=period_start,
            period_end=period_end,
            churn_risk_score=Decimal("0.3"),
            days_active_in_period=20,
            plan_utilization_percentage=Decimal("50.0")
        )
        
        assert billing_analytics.is_at_risk is False
    
    def test_calculate_customer_health_score(self):
        """Test customer health score calculation."""
        period_start = datetime.utcnow()
        period_end = period_start + timedelta(days=30)
        
        billing_analytics = BillingAnalytics(
            period_start=period_start,
            period_end=period_end,
            plan_utilization_percentage=Decimal("80.0"),
            days_active_in_period=24,  # 80% of 30 days
            avg_sessions_per_active_day=Decimal("5.0"),
            success_rate_percentage=Decimal("95.0")
        )
        
        health_score = billing_analytics.calculate_customer_health_score()
        
        # Expected: (80 * 0.3) + (80 * 0.3) + (50 * 0.2) + (95 * 0.2) = 24 + 24 + 10 + 19 = 77
        assert 75 <= health_score <= 80  # Allow some tolerance for floating point
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        user_id = uuid4()
        period_start = datetime.utcnow().replace(microsecond=0)
        period_end = period_start + timedelta(days=30)
        
        billing_analytics = BillingAnalytics(
            user_id=user_id,
            period_type="monthly",
            period_start=period_start,
            period_end=period_end,
            plan_name="PRO",
            total_revenue_usd=Decimal("99.99"),
            total_minutes_processed=Decimal("500.0"),
            sessions_created=10,
            transcriptions_completed=15,
            exports_by_format={"csv": 5, "pdf": 3}
        )
        
        data = billing_analytics.to_dict()
        
        assert data["user_id"] == str(user_id)
        assert data["period"]["type"] == "monthly"
        assert data["period"]["start"] == period_start.isoformat()
        assert data["period"]["end"] == period_end.isoformat()
        assert data["plan_info"]["current_plan"] == "PRO"
        assert data["revenue"]["total"] == 99.99
        assert data["usage"]["total_minutes"] == 500.0
        assert data["usage"]["sessions_created"] == 10
        assert data["usage"]["transcriptions_completed"] == 15
        assert data["exports"]["by_format"] == {"csv": 5, "pdf": 3}
    
    def test_create_from_usage_data(self):
        """Test creating BillingAnalytics from usage data."""
        user_id = uuid4()
        period_start = datetime.utcnow()
        period_end = period_start + timedelta(days=30)
        
        usage_data = {
            "plan_name": "PRO",
            "sessions_created": 20,
            "transcriptions_completed": 25,
            "total_minutes_processed": 600,
            "plan_utilization": 85.5
        }
        
        revenue_data = {
            "total_revenue": 149.99,
            "subscription_revenue": 99.99,
            "overage_revenue": 50.00
        }
        
        user_profile = {
            "signup_date": datetime.utcnow() - timedelta(days=180),
            "tenure_days": 180,
            "segment": "power"
        }
        
        billing_analytics = BillingAnalytics.create_from_usage_data(
            user_id=user_id,
            period_type="monthly",
            period_start=period_start,
            period_end=period_end,
            usage_data=usage_data,
            revenue_data=revenue_data,
            user_profile=user_profile
        )
        
        assert billing_analytics.user_id == user_id
        assert billing_analytics.period_type == "monthly"
        assert billing_analytics.plan_name == "PRO"
        assert billing_analytics.sessions_created == 20
        assert billing_analytics.transcriptions_completed == 25
        assert billing_analytics.total_minutes_processed == Decimal("600")
        assert billing_analytics.plan_utilization_percentage == Decimal("85.5")
        assert billing_analytics.total_revenue_usd == Decimal("149.99")
        assert billing_analytics.subscription_revenue_usd == Decimal("99.99")
        assert billing_analytics.usage_overage_usd == Decimal("50.00")
        assert billing_analytics.user_tenure_days == 180
        assert billing_analytics.user_segment == "power"