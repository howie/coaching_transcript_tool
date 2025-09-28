"""
Payment success rate monitoring validation tests.
Tests the monitoring, metrics collection, and alerting systems for payment success rates.
"""

import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

# Import modules with error handling
try:
    from coaching_assistant.services.monitoring_service import (
        PaymentMonitoringService,
    )
except ImportError:
    # Mock class if not available
    class PaymentMonitoringService:
        def __init__(self, db_session):
            self.db = db_session


try:
    from coaching_assistant.core.services.ecpay_service import (
        ECPaySubscriptionService,
    )
except ImportError:

    class ECPaySubscriptionService:
        def __init__(self, db_session, config):
            self.db = db_session


try:
    from coaching_assistant.models import (
        PaymentStatus,
        SaasSubscription,
        SubscriptionPayment,
        SubscriptionStatus,
        WebhookLog,
    )
except ImportError:
    # Mock enums and models for testing
    from enum import Enum

    class PaymentStatus(Enum):
        SUCCESS = "success"
        FAILED = "failed"
        PENDING = "pending"

    class SubscriptionStatus(Enum):
        ACTIVE = "active"
        PAST_DUE = "past_due"
        CANCELLED = "cancelled"

    class SubscriptionPayment:
        pass

    class SaasSubscription:
        pass

    class WebhookLog:
        pass


class TestPaymentSuccessRateMonitoring:
    """Test payment success rate monitoring and alerting."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session for testing."""
        return Mock()

    @pytest.fixture
    def monitoring_service(self, mock_db_session):
        """Create monitoring service instance."""
        return PaymentMonitoringService(mock_db_session)

    def test_payment_success_rate_calculation(
        self, monitoring_service, mock_db_session
    ):
        """Test accurate payment success rate calculation."""

        # Mock payment data for last 24 hours
        mock_payments = [
            Mock(
                status=PaymentStatus.SUCCESS.value,
                created_at=datetime.now() - timedelta(hours=1),
            ),
            Mock(
                status=PaymentStatus.SUCCESS.value,
                created_at=datetime.now() - timedelta(hours=2),
            ),
            Mock(
                status=PaymentStatus.SUCCESS.value,
                created_at=datetime.now() - timedelta(hours=3),
            ),
            Mock(
                status=PaymentStatus.FAILED.value,
                created_at=datetime.now() - timedelta(hours=4),
            ),
            Mock(
                status=PaymentStatus.SUCCESS.value,
                created_at=datetime.now() - timedelta(hours=5),
            ),
        ]

        mock_db_session.query.return_value.filter.return_value.all.return_value = (
            mock_payments
        )

        # Calculate success rate
        success_rate = monitoring_service.calculate_payment_success_rate(
            period_hours=24
        )

        # Expected: 4 successful out of 5 total = 80%
        assert success_rate == 80.0, f"Expected 80% success rate, got {success_rate}%"

    def test_payment_success_rate_over_time(self, monitoring_service, mock_db_session):
        """Test payment success rate calculation over different time periods."""

        # Mock payments across different time periods
        now = datetime.now()

        # Last hour: 2 success, 0 failures = 100%
        last_hour = [
            Mock(
                status=PaymentStatus.SUCCESS.value,
                created_at=now - timedelta(minutes=30),
            ),
            Mock(
                status=PaymentStatus.SUCCESS.value,
                created_at=now - timedelta(minutes=45),
            ),
        ]

        # Last 24 hours: 8 success, 2 failures = 80%
        last_24_hours = last_hour + [
            Mock(
                status=PaymentStatus.SUCCESS.value,
                created_at=now - timedelta(hours=2),
            ),
            Mock(
                status=PaymentStatus.SUCCESS.value,
                created_at=now - timedelta(hours=4),
            ),
            Mock(
                status=PaymentStatus.SUCCESS.value,
                created_at=now - timedelta(hours=6),
            ),
            Mock(
                status=PaymentStatus.SUCCESS.value,
                created_at=now - timedelta(hours=8),
            ),
            Mock(
                status=PaymentStatus.SUCCESS.value,
                created_at=now - timedelta(hours=12),
            ),
            Mock(
                status=PaymentStatus.SUCCESS.value,
                created_at=now - timedelta(hours=18),
            ),
            Mock(
                status=PaymentStatus.FAILED.value,
                created_at=now - timedelta(hours=10),
            ),
            Mock(
                status=PaymentStatus.FAILED.value,
                created_at=now - timedelta(hours=20),
            ),
        ]

        # Mock different query results based on time filter
        def mock_query_filter(*args):
            mock_query = Mock()
            if "hours=1" in str(args):
                mock_query.all.return_value = last_hour
            elif "hours=24" in str(args):
                mock_query.all.return_value = last_24_hours
            return mock_query

        mock_db_session.query.return_value.filter.side_effect = mock_query_filter

        # Test different periods
        hourly_rate = monitoring_service.calculate_payment_success_rate(period_hours=1)
        daily_rate = monitoring_service.calculate_payment_success_rate(period_hours=24)

        assert hourly_rate == 100.0, f"Hourly rate should be 100%, got {hourly_rate}%"
        assert daily_rate == 80.0, f"Daily rate should be 80%, got {daily_rate}%"

    def test_success_rate_threshold_alerting(self, monitoring_service, mock_db_session):
        """Test alerting when success rate falls below threshold."""

        # Mock low success rate scenario (60% - below 98% threshold)
        mock_payments = [Mock(status=PaymentStatus.SUCCESS.value) for _ in range(6)] + [
            Mock(status=PaymentStatus.FAILED.value) for _ in range(4)
        ]

        mock_db_session.query.return_value.filter.return_value.all.return_value = (
            mock_payments
        )

        with patch.object(monitoring_service, "send_alert") as mock_alert:
            # Check if threshold breach is detected
            monitoring_service.check_payment_success_threshold(threshold=98.0)

            # Should trigger alert for low success rate
            mock_alert.assert_called_once()
            alert_call = mock_alert.call_args
            assert "success rate" in alert_call[1]["message"].lower()
            assert "60.0%" in alert_call[1]["message"]

    def test_webhook_processing_time_monitoring(
        self, monitoring_service, mock_db_session
    ):
        """Test monitoring of webhook processing times."""

        # Mock webhook logs with processing times
        mock_webhook_logs = [
            Mock(
                processing_time_ms=150,
                status="success",
                created_at=datetime.now() - timedelta(minutes=5),
            ),
            Mock(
                processing_time_ms=230,
                status="success",
                created_at=datetime.now() - timedelta(minutes=10),
            ),
            Mock(
                processing_time_ms=89,
                status="success",
                created_at=datetime.now() - timedelta(minutes=15),
            ),
            Mock(
                processing_time_ms=1200,
                status="success",
                created_at=datetime.now() - timedelta(minutes=20),
            ),  # Slow
            Mock(
                processing_time_ms=340,
                status="success",
                created_at=datetime.now() - timedelta(minutes=25),
            ),
        ]

        mock_db_session.query.return_value.filter.return_value.all.return_value = (
            mock_webhook_logs
        )

        # Calculate average processing time
        avg_processing_time = (
            monitoring_service.calculate_average_webhook_processing_time(period_hours=1)
        )

        # Expected: (150 + 230 + 89 + 1200 + 340) / 5 = 401.8ms
        expected_avg = (150 + 230 + 89 + 1200 + 340) / 5
        assert abs(avg_processing_time - expected_avg) < 0.1, (
            f"Expected ~{expected_avg}ms, got {avg_processing_time}ms"
        )

    def test_webhook_failure_rate_monitoring(self, monitoring_service, mock_db_session):
        """Test monitoring webhook failure rates."""

        # Mock webhook logs with mixed success/failure
        mock_webhooks = [
            Mock(status="success", webhook_type="billing_callback"),
            Mock(status="success", webhook_type="billing_callback"),
            Mock(status="success", webhook_type="auth_callback"),
            Mock(status="failed", webhook_type="billing_callback"),
            Mock(status="success", webhook_type="billing_callback"),
            Mock(status="failed", webhook_type="auth_callback"),
        ]

        mock_db_session.query.return_value.filter.return_value.all.return_value = (
            mock_webhooks
        )

        # Calculate failure rate
        failure_rate = monitoring_service.calculate_webhook_failure_rate(
            period_hours=24
        )

        # Expected: 2 failures out of 6 total = 33.33%
        expected_rate = (2 / 6) * 100
        assert abs(failure_rate - expected_rate) < 0.1, (
            f"Expected ~{expected_rate}%, got {failure_rate}%"
        )

    def test_subscription_churn_rate_monitoring(
        self, monitoring_service, mock_db_session
    ):
        """Test subscription churn rate calculation."""

        # Mock subscription data for churn calculation
        start_of_month = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        # 100 active subscriptions at start of month
        # 5 cancelled during month = 5% churn rate
        # Mock cancelled subscriptions (unused in test but shows test intention)
        _ = [
            Mock(cancelled_at=start_of_month + timedelta(days=5)),
            Mock(cancelled_at=start_of_month + timedelta(days=10)),
            Mock(cancelled_at=start_of_month + timedelta(days=15)),
            Mock(cancelled_at=start_of_month + timedelta(days=20)),
            Mock(cancelled_at=start_of_month + timedelta(days=25)),
        ]

        # Mock query for cancelled subscriptions
        mock_db_session.query.return_value.filter.return_value.count.return_value = 5

        # Mock query for total active subscriptions at start of month
        mock_db_session.query.return_value.filter.return_value.filter.return_value.count.return_value = 100

        churn_rate = monitoring_service.calculate_monthly_churn_rate()

        # Expected: 5 cancelled out of 100 active = 5%
        assert churn_rate == 5.0, f"Expected 5% churn rate, got {churn_rate}%"

    def test_revenue_metrics_monitoring(self, monitoring_service, mock_db_session):
        """Test Monthly Recurring Revenue (MRR) monitoring."""

        # Mock active subscriptions with different plans
        mock_subscriptions = [
            Mock(
                plan_id="PRO",
                amount_twd=89900,
                status=SubscriptionStatus.ACTIVE.value,
            ),  # $899 TWD
            Mock(
                plan_id="PRO",
                amount_twd=89900,
                status=SubscriptionStatus.ACTIVE.value,
            ),
            Mock(
                plan_id="ENTERPRISE",
                amount_twd=299900,
                status=SubscriptionStatus.ACTIVE.value,
            ),  # $2999 TWD
            Mock(
                plan_id="PRO",
                amount_twd=89900,
                status=SubscriptionStatus.ACTIVE.value,
            ),
            Mock(
                plan_id="ENTERPRISE",
                amount_twd=299900,
                status=SubscriptionStatus.ACTIVE.value,
            ),
        ]

        mock_db_session.query.return_value.filter.return_value.all.return_value = (
            mock_subscriptions
        )

        mrr = monitoring_service.calculate_monthly_recurring_revenue()

        # Expected: (3 * 899) + (2 * 2999) = 2697 + 5998 = 8695 TWD
        expected_mrr = (3 * 899) + (2 * 2999)
        assert mrr == expected_mrr, f"Expected MRR {expected_mrr} TWD, got {mrr} TWD"

    def test_conversion_rate_monitoring(self, monitoring_service, mock_db_session):
        """Test free-to-paid conversion rate monitoring."""

        # Mock user conversion data
        # 10 users signed up, 2 converted to paid = 20% conversion
        # Mock conversions (unused in test but shows test intention)
        _ = [
            Mock(
                converted_at=datetime.now() - timedelta(days=5),
                from_plan="FREE",
                to_plan="PRO",
            ),
            Mock(
                converted_at=datetime.now() - timedelta(days=10),
                from_plan="FREE",
                to_plan="ENTERPRISE",
            ),
        ]

        # mock_new_users = 10  # Total new users in period (handled by mock)

        # Mock queries
        mock_db_session.query.return_value.filter.return_value.count.side_effect = [
            2,
            10,
        ]  # conversions, new users

        conversion_rate = monitoring_service.calculate_conversion_rate(period_days=30)

        # Expected: 2 conversions out of 10 new users = 20%
        assert conversion_rate == 20.0, (
            f"Expected 20% conversion rate, got {conversion_rate}%"
        )


class TestRealTimeMonitoring:
    """Test real-time monitoring capabilities."""

    @pytest.fixture
    def monitoring_service(self, mock_db_session):
        return PaymentMonitoringService(mock_db_session)

    def test_real_time_payment_status_tracking(
        self, monitoring_service, mock_db_session
    ):
        """Test real-time tracking of payment status changes."""

        # Simulate payment status change event
        payment_event = {
            "payment_id": "pay_123",
            "old_status": PaymentStatus.PENDING.value,
            "new_status": PaymentStatus.SUCCESS.value,
            "timestamp": datetime.now(),
            "processing_time_ms": 250,
        }

        with patch.object(monitoring_service, "emit_payment_metric") as mock_emit:
            monitoring_service.track_payment_status_change(payment_event)

            # Should emit real-time metric
            mock_emit.assert_called_once()
            metric = mock_emit.call_args[0][0]
            assert metric["type"] == "payment_success"
            assert metric["processing_time_ms"] == 250

    def test_webhook_response_time_tracking(self, monitoring_service):
        """Test real-time webhook response time tracking."""

        # Simulate webhook processing
        webhook_start = time.time()
        time.sleep(0.1)  # Simulate 100ms processing
        webhook_end = time.time()

        processing_time = (webhook_end - webhook_start) * 1000  # Convert to ms

        with patch.object(
            monitoring_service, "record_webhook_processing_time"
        ) as mock_record:
            monitoring_service.track_webhook_processing(
                "billing_callback", processing_time, "success"
            )

            mock_record.assert_called_once_with(
                "billing_callback", processing_time, "success"
            )

    def test_alert_threshold_breaches(self, monitoring_service):
        """Test real-time alerting when thresholds are breached."""

        # Test different alert scenarios
        alert_scenarios = [
            {
                "metric": "payment_success_rate",
                "value": 95.0,
                "threshold": 98.0,
                "should_alert": True,
            },
            {
                "metric": "webhook_processing_time",
                "value": 800.0,  # ms
                "threshold": 500.0,
                "should_alert": True,
            },
            {
                "metric": "churn_rate",
                "value": 8.0,  # %
                "threshold": 5.0,
                "should_alert": True,
            },
            {
                "metric": "payment_success_rate",
                "value": 99.5,
                "threshold": 98.0,
                "should_alert": False,  # Above threshold
            },
        ]

        with patch.object(monitoring_service, "send_alert") as mock_alert:
            for scenario in alert_scenarios:
                monitoring_service.check_metric_threshold(
                    metric_name=scenario["metric"],
                    current_value=scenario["value"],
                    threshold=scenario["threshold"],
                )

                if scenario["should_alert"]:
                    # Verify alert was sent
                    assert mock_alert.called, (
                        f"Should alert for {scenario['metric']} = {scenario['value']}"
                    )
                    mock_alert.reset_mock()


class TestMonitoringDashboard:
    """Test monitoring dashboard data aggregation."""

    @pytest.fixture
    def monitoring_service(self, mock_db_session):
        return PaymentMonitoringService(mock_db_session)

    def test_dashboard_metrics_aggregation(self, monitoring_service, mock_db_session):
        """Test aggregation of metrics for monitoring dashboard."""

        # Mock various metric calculations
        with patch.object(
            monitoring_service,
            "calculate_payment_success_rate",
            return_value=97.5,
        ):
            with patch.object(
                monitoring_service,
                "calculate_average_webhook_processing_time",
                return_value=245.0,
            ):
                with patch.object(
                    monitoring_service,
                    "calculate_monthly_churn_rate",
                    return_value=4.2,
                ):
                    with patch.object(
                        monitoring_service,
                        "calculate_monthly_recurring_revenue",
                        return_value=125000,
                    ):
                        with patch.object(
                            monitoring_service,
                            "calculate_conversion_rate",
                            return_value=18.5,
                        ):
                            # Get dashboard metrics
                            dashboard_data = monitoring_service.get_dashboard_metrics()

                            # Verify all key metrics are included
                            assert dashboard_data["payment_success_rate"] == 97.5
                            assert (
                                dashboard_data["avg_webhook_processing_time"] == 245.0
                            )
                            assert dashboard_data["monthly_churn_rate"] == 4.2
                            assert dashboard_data["monthly_recurring_revenue"] == 125000
                            assert dashboard_data["conversion_rate"] == 18.5

                            # Verify health status calculation
                            assert "overall_health" in dashboard_data
                            assert dashboard_data["overall_health"] in [
                                "healthy",
                                "warning",
                                "critical",
                            ]

    def test_historical_metrics_trending(self, monitoring_service, mock_db_session):
        """Test historical metrics for trending analysis."""

        # Mock historical data points
        historical_success_rates = [
            98.5,
            97.8,
            99.1,
            96.5,
            97.2,
            98.9,
            97.5,
        ]  # Last 7 days

        with patch.object(
            monitoring_service,
            "get_historical_success_rates",
            return_value=historical_success_rates,
        ):
            trend_data = monitoring_service.get_success_rate_trend(days=7)

            # Should return trend direction
            assert "trend_direction" in trend_data
            assert trend_data["trend_direction"] in ["up", "down", "stable"]
            assert "data_points" in trend_data
            assert len(trend_data["data_points"]) == 7

    def test_alert_summary_generation(self, monitoring_service):
        """Test generation of alert summaries for dashboard."""

        # Mock recent alerts
        mock_alerts = [
            {
                "timestamp": datetime.now() - timedelta(hours=2),
                "severity": "warning",
                "metric": "payment_success_rate",
                "value": 96.5,
                "threshold": 98.0,
            },
            {
                "timestamp": datetime.now() - timedelta(hours=6),
                "severity": "critical",
                "metric": "webhook_processing_time",
                "value": 1200.0,
                "threshold": 500.0,
            },
        ]

        with patch.object(
            monitoring_service, "get_recent_alerts", return_value=mock_alerts
        ):
            alert_summary = monitoring_service.get_alert_summary(hours=24)

            # Should categorize alerts
            assert "total_alerts" in alert_summary
            assert alert_summary["total_alerts"] == 2
            assert "critical_alerts" in alert_summary
            assert alert_summary["critical_alerts"] == 1
            assert "warning_alerts" in alert_summary
            assert alert_summary["warning_alerts"] == 1


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = Mock()
    session.query.return_value.filter.return_value.all.return_value = []
    session.query.return_value.filter.return_value.count.return_value = 0
    return session


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
