"""Tests for BillingAnalyticsService."""

from datetime import datetime, UTC, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from coaching_assistant.models.billing_analytics import BillingAnalytics
from coaching_assistant.services.billing_analytics_service import (
    BillingAnalyticsService,
)


class TestBillingAnalyticsService:
    """Test BillingAnalyticsService functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = Mock()
        db.query.return_value = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.delete = Mock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create a BillingAnalyticsService instance with mock dependencies."""
        with patch(
            "coaching_assistant.services.billing_analytics_service.UsageAnalyticsService"
        ) as mock_usage_service:
            service = BillingAnalyticsService(mock_db)
            service.usage_analytics_service = mock_usage_service.return_value
            return service

    @pytest.fixture
    def sample_billing_data(self):
        """Create sample billing analytics data."""
        user_id = uuid4()
        period_start = datetime.now(UTC).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        return [
            BillingAnalytics(
                id=uuid4(),
                user_id=user_id,
                period_type="monthly",
                period_start=period_start,
                period_end=period_start + timedelta(days=30),
                plan_name="PRO",
                total_revenue_usd=Decimal("99.99"),
                subscription_revenue_usd=Decimal("99.99"),
                usage_overage_usd=Decimal("0.00"),
                one_time_fees_usd=Decimal("5.00"),
                total_minutes_processed=Decimal("500.0"),
                sessions_created=20,
                transcriptions_completed=25,
                total_provider_cost_usd=Decimal("25.00"),
                plan_utilization_percentage=Decimal("75.0"),
                churn_risk_score=Decimal("0.3"),
                success_rate_percentage=Decimal("95.0"),
                days_active_in_period=20,
            ),
            BillingAnalytics(
                id=uuid4(),
                user_id=uuid4(),
                period_type="monthly",
                period_start=period_start,
                period_end=period_start + timedelta(days=30),
                plan_name="FREE",
                total_revenue_usd=Decimal("0.00"),
                subscription_revenue_usd=Decimal("0.00"),
                usage_overage_usd=Decimal("0.00"),
                one_time_fees_usd=Decimal("0.00"),
                total_minutes_processed=Decimal("50.0"),
                sessions_created=5,
                transcriptions_completed=8,
                total_provider_cost_usd=Decimal("5.00"),
                plan_utilization_percentage=Decimal("25.0"),
                churn_risk_score=Decimal("0.8"),
                success_rate_percentage=Decimal("90.0"),
                days_active_in_period=8,
            ),
        ]

    def test_get_admin_overview(self, service, mock_db, sample_billing_data):
        """Test getting admin overview with sample data."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_billing_data
        mock_db.query.return_value = mock_query

        period_start = datetime.now(UTC) - timedelta(days=30)
        period_end = datetime.now(UTC)

        overview = service.get_admin_overview(period_start, period_end, "monthly")

        # Verify structure
        assert "revenue_metrics" in overview
        assert "usage_metrics" in overview
        assert "customer_segments" in overview
        assert "top_users" in overview
        assert "trend_data" in overview

        # Verify revenue metrics
        revenue_metrics = overview["revenue_metrics"]
        assert revenue_metrics["total_revenue"] == 99.99
        assert (
            revenue_metrics["gross_margin"] == 69.99
        )  # 99.99 - 30.00 (25.00 provider cost + 5.00 one-time fees)
        assert revenue_metrics["avg_revenue_per_user"] == 49.995  # 99.99 / 2 users

    def test_calculate_revenue_metrics(self, service, sample_billing_data):
        """Test revenue metrics calculation."""
        revenue_metrics = service._calculate_revenue_metrics(sample_billing_data)

        expected_total_revenue = 99.99  # Only PRO user has revenue
        expected_gross_margin = 69.99  # 99.99 - 30.00 (total costs)
        expected_avg_revenue_per_user = 49.995  # 99.99 / 2 users

        assert revenue_metrics["total_revenue"] == expected_total_revenue
        assert revenue_metrics["gross_margin"] == expected_gross_margin
        assert revenue_metrics["avg_revenue_per_user"] == expected_avg_revenue_per_user
        assert revenue_metrics["subscription_revenue"] == 99.99
        assert revenue_metrics["overage_revenue"] == 0.0

    def test_calculate_revenue_metrics_empty_data(self, service):
        """Test revenue metrics calculation with empty data."""
        revenue_metrics = service._calculate_revenue_metrics([])

        assert revenue_metrics["total_revenue"] == 0
        assert revenue_metrics["gross_margin"] == 0
        assert revenue_metrics["avg_revenue_per_user"] == 0
        assert revenue_metrics["subscription_revenue"] == 0
        assert revenue_metrics["overage_revenue"] == 0

    def test_calculate_usage_metrics(self, service, sample_billing_data):
        """Test usage metrics calculation."""
        usage_metrics = service._calculate_usage_metrics(sample_billing_data)

        expected_total_sessions = 25  # 20 + 5
        expected_total_transcriptions = 33  # 25 + 8
        expected_total_minutes = 550.0  # 500.0 + 50.0
        expected_avg_success_rate = 92.5  # (95.0 + 90.0) / 2

        assert usage_metrics["total_sessions"] == expected_total_sessions
        assert usage_metrics["total_transcriptions"] == expected_total_transcriptions
        assert usage_metrics["total_minutes"] == expected_total_minutes
        assert usage_metrics["success_rate"] == expected_avg_success_rate
        assert usage_metrics["unique_active_users"] == 2

    def test_get_revenue_trends(self, service, mock_db, sample_billing_data):
        """Test getting revenue trends."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = sample_billing_data
        mock_db.query.return_value = mock_query

        trends = service.get_revenue_trends("monthly", 12, "pro")

        assert isinstance(trends, list)
        # Should have at least one trend point
        if trends:
            trend = trends[0]
            assert "date" in trend
            assert "revenue" in trend
            assert "users" in trend
            assert "sessions" in trend
            assert "minutes" in trend

    def test_get_customer_segmentation(self, service, mock_db, sample_billing_data):
        """Test customer segmentation analysis."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_billing_data
        mock_db.query.return_value = mock_query

        period_start = datetime.now(UTC) - timedelta(days=30)
        period_end = datetime.now(UTC)

        segments = service.get_customer_segmentation(period_start, period_end, False)

        assert isinstance(segments, list)
        # Should analyze segments based on user_segment field
        for segment in segments:
            assert "segment" in segment
            assert "user_count" in segment
            assert "total_revenue" in segment

    def test_get_user_analytics_detail(self, service, mock_db):
        """Test getting detailed user analytics."""
        user_id = uuid4()

        # Mock user query
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.email = "test@example.com"
        mock_user.name = "Test User"
        mock_user.plan.value = "pro"
        mock_user.created_at = datetime.now(UTC) - timedelta(days=180)

        mock_user_query = Mock()
        mock_user_query.filter.return_value = mock_user_query
        mock_user_query.first.return_value = mock_user

        # Mock billing analytics query
        mock_billing_query = Mock()
        mock_billing_query.filter.return_value = mock_billing_query
        mock_billing_query.order_by.return_value = mock_billing_query
        mock_billing_query.all.return_value = []

        # Mock lifetime value query
        mock_ltv_query = Mock()
        mock_ltv_query.filter.return_value = mock_ltv_query
        mock_ltv_query.scalar.return_value = 250.00  # Mock lifetime value

        mock_db.query.side_effect = [
            mock_user_query,
            mock_billing_query,
            mock_ltv_query,
        ]

        # Mock usage analytics service
        service.usage_analytics_service.predict_usage.return_value = {
            "predicted_sessions": 30
        }
        service.usage_analytics_service.generate_insights.return_value = [
            {"type": "test"}
        ]

        detail = service.get_user_analytics_detail(user_id, True, True, 12)

        assert detail["user_id"] == user_id
        assert detail["user_email"] == "test@example.com"
        assert detail["user_name"] == "Test User"
        assert detail["current_plan"] == "pro"
        assert "historical_data" in detail
        assert "predictions" in detail
        assert "insights" in detail
        assert detail["tenure_days"] == 180

    def test_get_user_analytics_detail_user_not_found(self, service, mock_db):
        """Test getting user analytics when user doesn't exist."""
        user_id = uuid4()

        # Mock user not found
        mock_user_query = Mock()
        mock_user_query.filter.return_value = mock_user_query
        mock_user_query.first.return_value = None
        mock_db.query.return_value = mock_user_query

        with pytest.raises(ValueError, match=f"User {user_id} not found"):
            service.get_user_analytics_detail(user_id)

    def test_export_analytics_data_csv(self, service, mock_db, sample_billing_data):
        """Test exporting analytics data to CSV format."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_billing_data
        mock_db.query.return_value = mock_query

        period_start = datetime.now(UTC) - timedelta(days=30)
        period_end = datetime.now(UTC)

        export_result = service.export_analytics_data(
            "csv", period_start, period_end, False
        )

        assert export_result["format"] == "csv"
        assert "data" in export_result
        assert export_result["total_records"] == 2
        assert isinstance(export_result["data"], str)
        # CSV should contain headers
        assert "user_id" in export_result["data"]

    def test_export_analytics_data_json(self, service, mock_db, sample_billing_data):
        """Test exporting analytics data to JSON format."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_billing_data
        mock_db.query.return_value = mock_query

        period_start = datetime.now(UTC) - timedelta(days=30)
        period_end = datetime.now(UTC)

        export_result = service.export_analytics_data(
            "json", period_start, period_end, False
        )

        assert export_result["format"] == "json"
        assert "data" in export_result
        assert export_result["total_records"] == 2
        assert isinstance(export_result["data"], list)
        assert len(export_result["data"]) == 2

    def test_export_analytics_data_with_user_details(
        self, service, mock_db, sample_billing_data
    ):
        """Test exporting analytics data with user details."""
        # Mock database queries
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_billing_data

        # Mock user queries
        mock_user = Mock()
        mock_user.email = "test@example.com"
        mock_user.name = "Test User"
        mock_user.created_at = datetime.now(UTC)

        mock_user_query = Mock()
        mock_user_query.filter.return_value = mock_user_query
        mock_user_query.first.return_value = mock_user

        mock_db.query.side_effect = [mock_query] + [mock_user_query] * len(
            sample_billing_data
        )

        period_start = datetime.now(UTC) - timedelta(days=30)
        period_end = datetime.now(UTC)

        export_result = service.export_analytics_data(
            "json", period_start, period_end, True
        )

        assert export_result["format"] == "json"
        assert export_result["total_records"] == 2

        # Check that user details are included
        first_record = export_result["data"][0]
        assert "user_email" in first_record
        assert "user_name" in first_record
        assert first_record["user_email"] == "test@example.com"
        assert first_record["user_name"] == "Test User"

    def test_refresh_user_analytics_new_record(self, service, mock_db):
        """Test refreshing analytics for a user (new record)."""
        user_id = uuid4()

        # Mock no existing record
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        # Mock usage data calculation
        usage_data = {
            "sessions_created": 10,
            "total_minutes_processed": 300,
            "plan_name": "PRO",
        }
        service._calculate_user_billing_data = Mock(return_value=usage_data)

        result = service.refresh_user_analytics(user_id, "monthly", False)

        assert result["records_updated"] == 1
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_refresh_user_analytics_existing_record(self, service, mock_db):
        """Test refreshing analytics for a user (existing record)."""
        user_id = uuid4()

        # Mock existing record
        existing_record = Mock()
        existing_record.sessions_created = 5

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = existing_record
        mock_db.query.return_value = mock_query

        # Mock usage data calculation
        usage_data = {
            "sessions_created": 10,
            "total_minutes_processed": 300,
            "plan_name": "PRO",
        }
        service._calculate_user_billing_data = Mock(return_value=usage_data)

        result = service.refresh_user_analytics(user_id, "monthly", False)

        assert result["records_updated"] == 1
        assert existing_record.sessions_created == 10
        mock_db.commit.assert_called_once()

    def test_refresh_all_analytics(self, service, mock_db):
        """Test refreshing analytics for all users."""
        # Mock users
        users = [Mock(id=uuid4()) for _ in range(3)]
        mock_user_query = Mock()
        mock_user_query.all.return_value = users
        mock_db.query.return_value = mock_user_query

        # Mock refresh_user_analytics
        service.refresh_user_analytics = Mock(return_value={"records_updated": 1})

        result = service.refresh_all_analytics("monthly", False)

        assert result["users_processed"] == 3
        assert result["records_updated"] == 3
        assert service.refresh_user_analytics.call_count == 3

    def test_get_health_score_distribution(self, service, mock_db, sample_billing_data):
        """Test getting health score distribution."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_billing_data
        mock_db.query.return_value = mock_query

        distribution = service.get_health_score_distribution()

        assert "total_users" in distribution
        assert "score_ranges" in distribution
        assert "avg_health_score" in distribution
        assert "at_risk_users" in distribution
        assert "power_users" in distribution

        assert distribution["total_users"] == 2
        assert isinstance(distribution["score_ranges"], dict)
        assert isinstance(distribution["avg_health_score"], float)

    def test_get_health_score_distribution_empty_data(self, service, mock_db):
        """Test health score distribution with empty data."""
        # Mock empty query result
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        distribution = service.get_health_score_distribution()

        assert distribution["total_users"] == 0
        assert distribution["avg_health_score"] == 0
        assert distribution["at_risk_users"] == 0
        assert distribution["power_users"] == 0

    def test_determine_user_segment(self, service, mock_db):
        """Test user segmentation logic."""
        user_id = uuid4()

        # Mock usage history data for a power user
        usage_records = [
            Mock(
                audio_minutes_processed=Decimal("400.0"),
                utilization_percentage=85.0,
            ),
            Mock(
                audio_minutes_processed=Decimal("450.0"),
                utilization_percentage=90.0,
            ),
        ]

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = usage_records
        mock_db.query.return_value = mock_query

        segment = service._determine_user_segment(user_id)

        # With high utilization and minutes, should be 'power' user
        assert segment == "power"

    def test_determine_user_segment_new_user(self, service, mock_db):
        """Test user segmentation for new user with no history."""
        user_id = uuid4()

        # Mock no usage history
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        segment = service._determine_user_segment(user_id)

        assert segment == "new"

    @patch("coaching_assistant.services.billing_analytics_service.StringIO")
    @patch("coaching_assistant.services.billing_analytics_service.csv")
    def test_export_to_csv(self, mock_csv, mock_stringio, service):
        """Test CSV export functionality."""
        mock_output = Mock()
        mock_stringio.return_value = mock_output
        mock_output.getvalue.return_value = "csv,data"

        mock_writer = Mock()
        mock_csv.DictWriter.return_value = mock_writer

        data = [{"id": "1", "value": "test"}]
        result = service._export_to_csv(data)

        assert result["format"] == "csv"
        assert result["data"] == "csv,data"
        assert result["total_records"] == 1

        mock_csv.DictWriter.assert_called_once()
        mock_writer.writeheader.assert_called_once()
        mock_writer.writerows.assert_called_once_with(data)

    def test_export_to_csv_empty_data(self, service):
        """Test CSV export with empty data."""
        result = service._export_to_csv([])

        assert result["format"] == "csv"
        assert result["data"] == ""
        assert result["total_records"] == 0
