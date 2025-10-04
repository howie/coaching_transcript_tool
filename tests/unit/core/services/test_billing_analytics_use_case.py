"""Tests for billing analytics use cases - Day 2 Coverage Improvement.

Focus on improving coverage from 34% → 55% by testing all 10 use case classes.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock
from uuid import uuid4

import pytest

from coaching_assistant.core.services.billing_analytics_use_case import (
    BillingAnalyticsChurnUseCase,
    BillingAnalyticsCohortUseCase,
    BillingAnalyticsExportUseCase,
    BillingAnalyticsHealthScoreUseCase,
    BillingAnalyticsOverviewUseCase,
    BillingAnalyticsPlanPerformanceUseCase,
    BillingAnalyticsRefreshUseCase,
    BillingAnalyticsRevenueUseCase,
    BillingAnalyticsSegmentationUseCase,
    BillingAnalyticsUserDetailUseCase,
)


class TestBillingAnalyticsOverviewUseCase:
    """Test BillingAnalyticsOverviewUseCase."""

    @pytest.fixture
    def mock_service(self):
        """Create mock billing analytics service."""
        return Mock()

    @pytest.fixture
    def use_case(self, mock_service):
        """Create use case instance."""
        return BillingAnalyticsOverviewUseCase(mock_service)

    def test_execute_daily_period(self, use_case, mock_service):
        """Test overview with daily period type."""
        # Arrange
        mock_service.get_admin_overview.return_value = {"total_revenue": 1000}
        end_date = datetime.now(UTC)

        # Act
        result = use_case.execute("daily", 7, end_date)

        # Assert
        assert "period_start" in result
        assert "period_end" in result
        assert "overview" in result
        assert result["overview"]["total_revenue"] == 1000
        # Verify period calculation (7 days)
        assert (result["period_end"] - result["period_start"]).days == 7

    def test_execute_weekly_period(self, use_case, mock_service):
        """Test overview with weekly period type."""
        # Arrange
        mock_service.get_admin_overview.return_value = {"total_revenue": 5000}

        # Act
        result = use_case.execute("weekly", 4)  # 4 weeks

        # Assert
        assert "overview" in result
        # 4 weeks = 28 days
        assert (result["period_end"] - result["period_start"]).days == 28

    def test_execute_monthly_period(self, use_case, mock_service):
        """Test overview with monthly period type."""
        # Arrange
        mock_service.get_admin_overview.return_value = {"total_revenue": 20000}

        # Act
        result = use_case.execute("monthly", 3)  # 3 months

        # Assert
        assert "overview" in result
        # 3 months ≈ 90 days
        assert (result["period_end"] - result["period_start"]).days == 90

    def test_execute_quarterly_period(self, use_case, mock_service):
        """Test overview with quarterly period type."""
        # Arrange
        mock_service.get_admin_overview.return_value = {"total_revenue": 50000}

        # Act
        result = use_case.execute("quarterly", 2)  # 2 quarters

        # Assert
        assert "overview" in result
        # 2 quarters = 180 days
        assert (result["period_end"] - result["period_start"]).days == 180

    def test_execute_default_period_type(self, use_case, mock_service):
        """Test overview with unknown period type defaults to monthly."""
        # Arrange
        mock_service.get_admin_overview.return_value = {"total_revenue": 10000}

        # Act
        result = use_case.execute("unknown", 2)

        # Assert
        # Should default to monthly (2 * 30 = 60 days)
        assert (result["period_end"] - result["period_start"]).days == 60

    def test_execute_default_end_date(self, use_case, mock_service):
        """Test overview with default end date (now)."""
        # Arrange
        mock_service.get_admin_overview.return_value = {}
        before_call = datetime.now(UTC)

        # Act
        result = use_case.execute("daily", 1)

        # Assert
        after_call = datetime.now(UTC)
        assert before_call <= result["period_end"] <= after_call


class TestBillingAnalyticsRevenueUseCase:
    """Test BillingAnalyticsRevenueUseCase."""

    @pytest.fixture
    def mock_service(self):
        return Mock()

    @pytest.fixture
    def use_case(self, mock_service):
        return BillingAnalyticsRevenueUseCase(mock_service)

    def test_execute_without_plan_filter(self, use_case, mock_service):
        """Test revenue trends without plan filtering."""
        # Arrange
        mock_service.get_revenue_trends.return_value = [
            {"month": "2024-01", "revenue": 1000}
        ]

        # Act
        result = use_case.execute("monthly", 6)

        # Assert
        assert result["period_type"] == "monthly"
        assert result["months_included"] == 6
        assert result["plan_filter"] is None
        assert len(result["data"]) == 1

    def test_execute_with_plan_filter(self, use_case, mock_service):
        """Test revenue trends with specific plan filter."""
        # Arrange
        mock_service.get_revenue_trends.return_value = [
            {"month": "2024-01", "revenue": 500}
        ]

        # Act
        result = use_case.execute("monthly", 3, "PROFESSIONAL")

        # Assert
        assert result["plan_filter"] == "PROFESSIONAL"
        mock_service.get_revenue_trends.assert_called_once_with(
            "monthly", 3, "PROFESSIONAL"
        )


class TestBillingAnalyticsSegmentationUseCase:
    """Test BillingAnalyticsSegmentationUseCase."""

    @pytest.fixture
    def mock_service(self):
        return Mock()

    @pytest.fixture
    def use_case(self, mock_service):
        return BillingAnalyticsSegmentationUseCase(mock_service)

    def test_execute_with_defaults(self, use_case, mock_service):
        """Test segmentation with default period (None → last 90 days)."""
        # Arrange
        mock_service.get_customer_segmentation.return_value = {"segments": []}

        # Act
        result = use_case.execute()

        # Assert
        assert "period_start" in result
        assert "period_end" in result
        assert "segments" in result

    def test_execute_with_custom_period(self, use_case, mock_service):
        """Test segmentation with custom period."""
        # Arrange
        start = datetime.now(UTC) - timedelta(days=60)
        end = datetime.now(UTC)
        mock_service.get_customer_segmentation.return_value = {"segments": []}

        # Act
        use_case.execute(start, end)

        # Assert
        mock_service.get_customer_segmentation.assert_called_once_with(
            start, end, False
        )

    def test_execute_with_predictions(self, use_case, mock_service):
        """Test segmentation with predictions enabled."""
        # Arrange
        mock_service.get_customer_segmentation.return_value = {
            "segments": [],
            "predictions": [],
        }

        # Act
        use_case.execute(include_predictions=True)

        # Assert
        mock_service.get_customer_segmentation.assert_called_once()
        call_args = mock_service.get_customer_segmentation.call_args
        assert call_args[0][2] is True  # include_predictions=True


class TestBillingAnalyticsUserDetailUseCase:
    """Test BillingAnalyticsUserDetailUseCase."""

    @pytest.fixture
    def mock_service(self):
        return Mock()

    @pytest.fixture
    def use_case(self, mock_service):
        return BillingAnalyticsUserDetailUseCase(mock_service)

    def test_execute_with_defaults(self, use_case, mock_service):
        """Test user detail with default parameters."""
        # Arrange
        user_id = uuid4()
        mock_service.get_user_analytics_detail.return_value = {"user_id": str(user_id)}

        # Act
        use_case.execute(user_id)

        # Assert
        mock_service.get_user_analytics_detail.assert_called_once_with(
            user_id, True, True, 12
        )

    def test_execute_without_predictions(self, use_case, mock_service):
        """Test user detail without predictions."""
        # Arrange
        user_id = uuid4()
        mock_service.get_user_analytics_detail.return_value = {}

        # Act
        use_case.execute(user_id, include_predictions=False)

        # Assert
        call_args = mock_service.get_user_analytics_detail.call_args[0]
        assert call_args[1] is False  # include_predictions

    def test_execute_without_insights(self, use_case, mock_service):
        """Test user detail without insights."""
        # Arrange
        user_id = uuid4()
        mock_service.get_user_analytics_detail.return_value = {}

        # Act
        use_case.execute(user_id, include_insights=False)

        # Assert
        call_args = mock_service.get_user_analytics_detail.call_args[0]
        assert call_args[2] is False  # include_insights

    def test_execute_custom_historical_months(self, use_case, mock_service):
        """Test user detail with custom historical months."""
        # Arrange
        user_id = uuid4()
        mock_service.get_user_analytics_detail.return_value = {}

        # Act
        use_case.execute(user_id, historical_months=24)

        # Assert
        call_args = mock_service.get_user_analytics_detail.call_args[0]
        assert call_args[3] == 24  # historical_months


class TestBillingAnalyticsCohortUseCase:
    """Test BillingAnalyticsCohortUseCase."""

    @pytest.fixture
    def mock_service(self):
        return Mock()

    @pytest.fixture
    def use_case(self, mock_service):
        return BillingAnalyticsCohortUseCase(mock_service)

    def test_execute_cohort_analysis(self, use_case, mock_service):
        """Test cohort analysis execution."""
        # Arrange
        mock_service.get_cohort_analysis.return_value = [
            {"cohort": "2024-01", "retention": 0.8}
        ]

        # Act
        result = use_case.execute("monthly", 12, "retention")

        # Assert
        assert result["cohort_type"] == "monthly"
        assert result["cohort_size"] == 12
        assert result["metric"] == "retention"
        assert len(result["data"]) == 1
        mock_service.get_cohort_analysis.assert_called_once_with(
            "monthly", 12, "retention"
        )


class TestBillingAnalyticsChurnUseCase:
    """Test BillingAnalyticsChurnUseCase."""

    @pytest.fixture
    def mock_service(self):
        return Mock()

    @pytest.fixture
    def use_case(self, mock_service):
        return BillingAnalyticsChurnUseCase(mock_service)

    def test_execute_without_predictions(self, use_case, mock_service):
        """Test churn analysis without predictions."""
        # Arrange
        mock_service.get_churn_analysis.return_value = {
            "summary": {},
            "at_risk_users": [],
            "recommendations": [],
        }

        # Act
        result = use_case.execute(0.7, 6, include_predictions=False)

        # Assert
        assert result["risk_threshold"] == 0.7
        assert result["analysis_period"]["months"] == 6
        assert result["predictions"] is None

    def test_execute_with_predictions(self, use_case, mock_service):
        """Test churn analysis with predictions."""
        # Arrange
        mock_service.get_churn_analysis.return_value = {
            "summary": {},
            "at_risk_users": [],
            "recommendations": [],
            "predictions": {"next_month_churn": 0.05},
        }

        # Act
        result = use_case.execute(0.7, 3, include_predictions=True)

        # Assert
        assert result["predictions"] is not None
        assert "next_month_churn" in result["predictions"]

    def test_execute_period_calculation(self, use_case, mock_service):
        """Test period calculation for churn analysis."""
        # Arrange
        mock_service.get_churn_analysis.return_value = {
            "summary": {},
            "at_risk_users": [],
            "recommendations": [],
        }

        # Act
        use_case.execute(0.8, 12)

        # Assert
        # Verify period calculation (12 months ≈ 360 days)
        call_args = mock_service.get_churn_analysis.call_args[0]
        start_date = call_args[0]
        end_date = call_args[1]
        days_diff = (end_date - start_date).days
        assert 355 <= days_diff <= 365  # Allow some tolerance


class TestBillingAnalyticsPlanPerformanceUseCase:
    """Test BillingAnalyticsPlanPerformanceUseCase."""

    @pytest.fixture
    def mock_service(self):
        return Mock()

    @pytest.fixture
    def use_case(self, mock_service):
        return BillingAnalyticsPlanPerformanceUseCase(mock_service)

    def test_execute_with_forecasts(self, use_case, mock_service):
        """Test plan performance with forecasts."""
        # Arrange
        mock_service.get_plan_performance_analysis.return_value = {
            "plans": [],
            "upgrade_patterns": [],
            "forecasts": {"next_month": 1000},
            "recommendations": [],
        }

        # Act
        result = use_case.execute(6, include_forecasts=True)

        # Assert
        assert result["forecasts"] is not None
        assert "next_month" in result["forecasts"]

    def test_execute_without_forecasts(self, use_case, mock_service):
        """Test plan performance without forecasts."""
        # Arrange
        mock_service.get_plan_performance_analysis.return_value = {
            "plans": [],
            "upgrade_patterns": [],
            "recommendations": [],
        }

        # Act
        result = use_case.execute(3, include_forecasts=False)

        # Assert
        assert result["forecasts"] is None

    def test_execute_period_months(self, use_case, mock_service):
        """Test different period months."""
        # Arrange
        mock_service.get_plan_performance_analysis.return_value = {
            "plans": [],
            "upgrade_patterns": [],
            "recommendations": [],
        }

        # Act
        result = use_case.execute(12)

        # Assert
        assert result["analysis_period"]["months"] == 12


class TestBillingAnalyticsExportUseCase:
    """Test BillingAnalyticsExportUseCase."""

    @pytest.fixture
    def mock_service(self):
        return Mock()

    @pytest.fixture
    def use_case(self, mock_service):
        return BillingAnalyticsExportUseCase(mock_service)

    def test_execute_with_defaults(self, use_case, mock_service):
        """Test export with default period (last 90 days)."""
        # Arrange
        mock_service.export_analytics_data.return_value = {"data": []}

        # Act
        use_case.execute("csv")

        # Assert
        mock_service.export_analytics_data.assert_called_once()
        call_args = mock_service.export_analytics_data.call_args[0]
        assert call_args[0] == "csv"
        assert call_args[3] is False  # include_user_details default

    def test_execute_with_custom_period(self, use_case, mock_service):
        """Test export with custom period."""
        # Arrange
        start = datetime.now(UTC) - timedelta(days=30)
        end = datetime.now(UTC)
        mock_service.export_analytics_data.return_value = {"data": []}

        # Act
        use_case.execute("json", start, end)

        # Assert
        call_args = mock_service.export_analytics_data.call_args[0]
        assert call_args[0] == "json"
        assert call_args[1] == start
        assert call_args[2] == end

    def test_execute_with_user_details(self, use_case, mock_service):
        """Test export with user details included."""
        # Arrange
        mock_service.export_analytics_data.return_value = {"data": [], "users": []}

        # Act
        use_case.execute("csv", include_user_details=True)

        # Assert
        call_args = mock_service.export_analytics_data.call_args[0]
        assert call_args[3] is True  # include_user_details


class TestBillingAnalyticsRefreshUseCase:
    """Test BillingAnalyticsRefreshUseCase."""

    @pytest.fixture
    def mock_service(self):
        return Mock()

    @pytest.fixture
    def use_case(self, mock_service):
        return BillingAnalyticsRefreshUseCase(mock_service)

    def test_execute_refresh_specific_user(self, use_case, mock_service):
        """Test refreshing analytics for specific user."""
        # Arrange
        user_id = uuid4()
        mock_service.refresh_user_analytics.return_value = {"records_updated": 5}

        # Act
        result = use_case.execute(user_id)

        # Assert
        assert result["success"] is True
        assert str(user_id) in result["message"]
        assert result["records_updated"] == 5
        mock_service.refresh_user_analytics.assert_called_once_with(
            user_id, "monthly", False
        )

    def test_execute_refresh_all_users(self, use_case, mock_service):
        """Test refreshing analytics for all users."""
        # Arrange
        mock_service.refresh_all_analytics.return_value = {
            "users_processed": 100,
            "records_updated": 500,
        }

        # Act
        result = use_case.execute()

        # Assert
        assert result["success"] is True
        assert "all users" in result["message"]
        assert result["users_processed"] == 100
        assert result["records_updated"] == 500
        mock_service.refresh_all_analytics.assert_called_once_with("monthly", False)

    def test_execute_with_force_rebuild(self, use_case, mock_service):
        """Test refresh with force rebuild."""
        # Arrange
        mock_service.refresh_all_analytics.return_value = {
            "users_processed": 50,
            "records_updated": 250,
        }

        # Act
        use_case.execute(force_rebuild=True)

        # Assert
        call_args = mock_service.refresh_all_analytics.call_args[0]
        assert call_args[1] is True  # force_rebuild

    def test_execute_with_custom_period_type(self, use_case, mock_service):
        """Test refresh with custom period type."""
        # Arrange
        user_id = uuid4()
        mock_service.refresh_user_analytics.return_value = {"records_updated": 3}

        # Act
        use_case.execute(user_id, period_type="weekly")

        # Assert
        call_args = mock_service.refresh_user_analytics.call_args[0]
        assert call_args[1] == "weekly"


class TestBillingAnalyticsHealthScoreUseCase:
    """Test BillingAnalyticsHealthScoreUseCase."""

    @pytest.fixture
    def mock_service(self):
        return Mock()

    @pytest.fixture
    def use_case(self, mock_service):
        return BillingAnalyticsHealthScoreUseCase(mock_service)

    def test_execute_health_score_distribution(self, use_case, mock_service):
        """Test health score distribution retrieval."""
        # Arrange
        mock_service.get_health_score_distribution.return_value = {
            "total_users": 100,
            "score_ranges": {
                "0-20": 5,
                "20-40": 10,
                "40-60": 30,
                "60-80": 40,
                "80-100": 15,
            },
            "avg_health_score": 65.5,
            "at_risk_users": 15,
            "power_users": 15,
        }

        # Act
        result = use_case.execute()

        # Assert
        assert result["total_users"] == 100
        assert result["avg_health_score"] == 65.5
        assert result["at_risk_users"] == 15
        assert result["power_users"] == 15
        assert len(result["score_ranges"]) == 5
        mock_service.get_health_score_distribution.assert_called_once()
