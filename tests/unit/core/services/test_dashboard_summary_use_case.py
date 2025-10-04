"""Tests for dashboard summary use case - Clean Architecture.

This test module focuses on error handling and edge cases for dashboard
summary business logic, following the test coverage improvement plan Day 3.

Target coverage: 35% → 60%
"""

from datetime import datetime
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from src.coaching_assistant.core.repositories.ports import (
    CoachingSessionRepoPort,
    SessionRepoPort,
)
from src.coaching_assistant.core.services.dashboard_summary_use_case import (
    DashboardSummaryRequest,
    DashboardSummaryResponse,
    DashboardSummaryUseCase,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def user_id() -> UUID:
    """Sample user ID for testing."""
    return uuid4()


@pytest.fixture
def mock_coaching_session_repo() -> Mock:
    """Mock coaching session repository."""
    return Mock(spec=CoachingSessionRepoPort)


@pytest.fixture
def mock_session_repo() -> Mock:
    """Mock session repository."""
    return Mock(spec=SessionRepoPort)


@pytest.fixture
def dashboard_use_case(
    mock_coaching_session_repo: Mock,
    mock_session_repo: Mock,
) -> DashboardSummaryUseCase:
    """Create DashboardSummaryUseCase instance."""
    return DashboardSummaryUseCase(
        coaching_session_repo=mock_coaching_session_repo,
        session_repo=mock_session_repo,
    )


# ============================================================================
# DashboardSummaryRequest Tests
# ============================================================================


class TestDashboardSummaryRequest:
    """Tests for DashboardSummaryRequest model."""

    def test_create_request_with_month(self, user_id: UUID):
        """Test creating request with specific month."""
        request = DashboardSummaryRequest(user_id=user_id, month="2025-10")

        assert request.user_id == user_id
        assert request.month == "2025-10"

    def test_create_request_without_month(self, user_id: UUID):
        """Test creating request without month (defaults to None)."""
        request = DashboardSummaryRequest(user_id=user_id)

        assert request.user_id == user_id
        assert request.month is None

    def test_create_request_with_explicit_none_month(self, user_id: UUID):
        """Test creating request with explicit None month."""
        request = DashboardSummaryRequest(user_id=user_id, month=None)

        assert request.user_id == user_id
        assert request.month is None


# ============================================================================
# DashboardSummaryResponse Tests
# ============================================================================


class TestDashboardSummaryResponse:
    """Tests for DashboardSummaryResponse model."""

    def test_create_response_with_all_fields(self):
        """Test creating response with all fields populated."""
        response = DashboardSummaryResponse(
            total_minutes=1000,
            current_month_minutes=120,
            transcripts_converted_count=15,
            current_month_revenue_by_currency={"USD": 10000, "TWD": 300000},
            unique_clients_total=8,
        )

        assert response.total_minutes == 1000
        assert response.current_month_minutes == 120
        assert response.transcripts_converted_count == 15
        assert response.current_month_revenue_by_currency == {
            "USD": 10000,
            "TWD": 300000,
        }
        assert response.unique_clients_total == 8

    def test_create_response_with_zero_values(self):
        """Test creating response with zero values (new user)."""
        response = DashboardSummaryResponse(
            total_minutes=0,
            current_month_minutes=0,
            transcripts_converted_count=0,
            current_month_revenue_by_currency={},
            unique_clients_total=0,
        )

        assert response.total_minutes == 0
        assert response.current_month_minutes == 0
        assert response.transcripts_converted_count == 0
        assert response.current_month_revenue_by_currency == {}
        assert response.unique_clients_total == 0

    def test_create_response_with_multiple_currencies(self):
        """Test response with multiple currencies."""
        revenue = {"USD": 5000, "TWD": 150000, "EUR": 4500}
        response = DashboardSummaryResponse(
            total_minutes=500,
            current_month_minutes=80,
            transcripts_converted_count=10,
            current_month_revenue_by_currency=revenue,
            unique_clients_total=5,
        )

        assert len(response.current_month_revenue_by_currency) == 3
        assert response.current_month_revenue_by_currency["USD"] == 5000
        assert response.current_month_revenue_by_currency["TWD"] == 150000
        assert response.current_month_revenue_by_currency["EUR"] == 4500


# ============================================================================
# DashboardSummaryUseCase Tests
# ============================================================================


class TestDashboardSummaryUseCase:
    """Tests for dashboard summary use case."""

    def test_execute_with_explicit_month(
        self,
        dashboard_use_case: DashboardSummaryUseCase,
        mock_coaching_session_repo: Mock,
        mock_session_repo: Mock,
        user_id: UUID,
    ):
        """Test execute with explicit month specified."""
        # Arrange
        mock_coaching_session_repo.get_total_minutes_for_user.return_value = 1500
        mock_coaching_session_repo.get_monthly_minutes_for_user.return_value = 200
        mock_session_repo.get_completed_count_for_user.return_value = 20
        mock_coaching_session_repo.get_monthly_revenue_by_currency.return_value = {
            "USD": 15000
        }
        mock_coaching_session_repo.get_unique_clients_count_for_user.return_value = 10

        request = DashboardSummaryRequest(user_id=user_id, month="2025-10")

        # Act
        response = dashboard_use_case.execute(request)

        # Assert
        assert response.total_minutes == 1500
        assert response.current_month_minutes == 200
        assert response.transcripts_converted_count == 20
        assert response.current_month_revenue_by_currency == {"USD": 15000}
        assert response.unique_clients_total == 10

        # Verify repository calls
        mock_coaching_session_repo.get_total_minutes_for_user.assert_called_once_with(
            user_id
        )
        mock_coaching_session_repo.get_monthly_minutes_for_user.assert_called_once_with(
            user_id, 2025, 10
        )
        mock_session_repo.get_completed_count_for_user.assert_called_once_with(user_id)
        mock_coaching_session_repo.get_monthly_revenue_by_currency.assert_called_once_with(
            user_id, 2025, 10
        )
        mock_coaching_session_repo.get_unique_clients_count_for_user.assert_called_once_with(
            user_id
        )

    def test_execute_without_month_uses_current_month(
        self,
        dashboard_use_case: DashboardSummaryUseCase,
        mock_coaching_session_repo: Mock,
        mock_session_repo: Mock,
        user_id: UUID,
    ):
        """Test execute without month defaults to current month."""
        # Arrange
        mock_coaching_session_repo.get_total_minutes_for_user.return_value = 800
        mock_coaching_session_repo.get_monthly_minutes_for_user.return_value = 100
        mock_session_repo.get_completed_count_for_user.return_value = 12
        mock_coaching_session_repo.get_monthly_revenue_by_currency.return_value = {
            "TWD": 200000
        }
        mock_coaching_session_repo.get_unique_clients_count_for_user.return_value = 6

        request = DashboardSummaryRequest(user_id=user_id)

        # Act
        response = dashboard_use_case.execute(request)

        # Assert
        now = datetime.now()
        expected_year = now.year
        expected_month = now.month

        assert response.total_minutes == 800
        assert response.current_month_minutes == 100

        # Verify current month was used
        mock_coaching_session_repo.get_monthly_minutes_for_user.assert_called_once_with(
            user_id, expected_year, expected_month
        )
        mock_coaching_session_repo.get_monthly_revenue_by_currency.assert_called_once_with(
            user_id, expected_year, expected_month
        )

    def test_execute_with_zero_data_new_user(
        self,
        dashboard_use_case: DashboardSummaryUseCase,
        mock_coaching_session_repo: Mock,
        mock_session_repo: Mock,
        user_id: UUID,
    ):
        """Test execute for brand new user with no data."""
        # Arrange - all repository methods return zero/empty
        mock_coaching_session_repo.get_total_minutes_for_user.return_value = 0
        mock_coaching_session_repo.get_monthly_minutes_for_user.return_value = 0
        mock_session_repo.get_completed_count_for_user.return_value = 0
        mock_coaching_session_repo.get_monthly_revenue_by_currency.return_value = {}
        mock_coaching_session_repo.get_unique_clients_count_for_user.return_value = 0

        request = DashboardSummaryRequest(user_id=user_id, month="2025-01")

        # Act
        response = dashboard_use_case.execute(request)

        # Assert
        assert response.total_minutes == 0
        assert response.current_month_minutes == 0
        assert response.transcripts_converted_count == 0
        assert response.current_month_revenue_by_currency == {}
        assert response.unique_clients_total == 0

    def test_execute_with_high_volume_data(
        self,
        dashboard_use_case: DashboardSummaryUseCase,
        mock_coaching_session_repo: Mock,
        mock_session_repo: Mock,
        user_id: UUID,
    ):
        """Test execute with high volume user data."""
        # Arrange - simulate heavy user
        mock_coaching_session_repo.get_total_minutes_for_user.return_value = 50000
        mock_coaching_session_repo.get_monthly_minutes_for_user.return_value = 5000
        mock_session_repo.get_completed_count_for_user.return_value = 500
        mock_coaching_session_repo.get_monthly_revenue_by_currency.return_value = {
            "USD": 100000,
            "TWD": 3000000,
        }
        mock_coaching_session_repo.get_unique_clients_count_for_user.return_value = 100

        request = DashboardSummaryRequest(user_id=user_id, month="2025-12")

        # Act
        response = dashboard_use_case.execute(request)

        # Assert
        assert response.total_minutes == 50000
        assert response.current_month_minutes == 5000
        assert response.transcripts_converted_count == 500
        assert response.unique_clients_total == 100

    def test_execute_with_january_month(
        self,
        dashboard_use_case: DashboardSummaryUseCase,
        mock_coaching_session_repo: Mock,
        mock_session_repo: Mock,
        user_id: UUID,
    ):
        """Test execute with January month (edge case for month parsing)."""
        # Arrange
        mock_coaching_session_repo.get_total_minutes_for_user.return_value = 100
        mock_coaching_session_repo.get_monthly_minutes_for_user.return_value = 50
        mock_session_repo.get_completed_count_for_user.return_value = 5
        mock_coaching_session_repo.get_monthly_revenue_by_currency.return_value = {
            "USD": 5000
        }
        mock_coaching_session_repo.get_unique_clients_count_for_user.return_value = 3

        request = DashboardSummaryRequest(user_id=user_id, month="2025-01")

        # Act
        dashboard_use_case.execute(request)

        # Assert - verify January (month 1) was parsed correctly
        mock_coaching_session_repo.get_monthly_minutes_for_user.assert_called_once_with(
            user_id, 2025, 1
        )
        mock_coaching_session_repo.get_monthly_revenue_by_currency.assert_called_once_with(
            user_id, 2025, 1
        )

    def test_execute_with_december_month(
        self,
        dashboard_use_case: DashboardSummaryUseCase,
        mock_coaching_session_repo: Mock,
        mock_session_repo: Mock,
        user_id: UUID,
    ):
        """Test execute with December month (edge case for month parsing)."""
        # Arrange
        mock_coaching_session_repo.get_total_minutes_for_user.return_value = 200
        mock_coaching_session_repo.get_monthly_minutes_for_user.return_value = 80
        mock_session_repo.get_completed_count_for_user.return_value = 10
        mock_coaching_session_repo.get_monthly_revenue_by_currency.return_value = {
            "TWD": 150000
        }
        mock_coaching_session_repo.get_unique_clients_count_for_user.return_value = 7

        request = DashboardSummaryRequest(user_id=user_id, month="2025-12")

        # Act
        dashboard_use_case.execute(request)

        # Assert - verify December (month 12) was parsed correctly
        mock_coaching_session_repo.get_monthly_minutes_for_user.assert_called_once_with(
            user_id, 2025, 12
        )
        mock_coaching_session_repo.get_monthly_revenue_by_currency.assert_called_once_with(
            user_id, 2025, 12
        )

    def test_execute_with_multiple_currencies_in_revenue(
        self,
        dashboard_use_case: DashboardSummaryUseCase,
        mock_coaching_session_repo: Mock,
        mock_session_repo: Mock,
        user_id: UUID,
    ):
        """Test execute with revenue in multiple currencies."""
        # Arrange
        mock_coaching_session_repo.get_total_minutes_for_user.return_value = 1200
        mock_coaching_session_repo.get_monthly_minutes_for_user.return_value = 150
        mock_session_repo.get_completed_count_for_user.return_value = 18
        mock_coaching_session_repo.get_monthly_revenue_by_currency.return_value = {
            "USD": 12000,
            "TWD": 360000,
            "EUR": 10000,
            "GBP": 9000,
        }
        mock_coaching_session_repo.get_unique_clients_count_for_user.return_value = 12

        request = DashboardSummaryRequest(user_id=user_id, month="2025-06")

        # Act
        response = dashboard_use_case.execute(request)

        # Assert
        assert len(response.current_month_revenue_by_currency) == 4
        assert response.current_month_revenue_by_currency["USD"] == 12000
        assert response.current_month_revenue_by_currency["TWD"] == 360000
        assert response.current_month_revenue_by_currency["EUR"] == 10000
        assert response.current_month_revenue_by_currency["GBP"] == 9000

    def test_execute_repository_integration(
        self,
        dashboard_use_case: DashboardSummaryUseCase,
        mock_coaching_session_repo: Mock,
        mock_session_repo: Mock,
        user_id: UUID,
    ):
        """Test that all repository methods are called correctly."""
        # Arrange
        mock_coaching_session_repo.get_total_minutes_for_user.return_value = 500
        mock_coaching_session_repo.get_monthly_minutes_for_user.return_value = 100
        mock_session_repo.get_completed_count_for_user.return_value = 8
        mock_coaching_session_repo.get_monthly_revenue_by_currency.return_value = {
            "USD": 8000
        }
        mock_coaching_session_repo.get_unique_clients_count_for_user.return_value = 5

        request = DashboardSummaryRequest(user_id=user_id, month="2025-03")

        # Act
        dashboard_use_case.execute(request)

        # Assert all repository methods were called exactly once
        assert mock_coaching_session_repo.get_total_minutes_for_user.call_count == 1
        assert mock_coaching_session_repo.get_monthly_minutes_for_user.call_count == 1
        assert mock_session_repo.get_completed_count_for_user.call_count == 1
        assert (
            mock_coaching_session_repo.get_monthly_revenue_by_currency.call_count == 1
        )
        assert (
            mock_coaching_session_repo.get_unique_clients_count_for_user.call_count == 1
        )

    def test_execute_handles_empty_revenue_dict(
        self,
        dashboard_use_case: DashboardSummaryUseCase,
        mock_coaching_session_repo: Mock,
        mock_session_repo: Mock,
        user_id: UUID,
    ):
        """Test execute when revenue dictionary is empty (no revenue this month)."""
        # Arrange
        mock_coaching_session_repo.get_total_minutes_for_user.return_value = 300
        mock_coaching_session_repo.get_monthly_minutes_for_user.return_value = 0
        mock_session_repo.get_completed_count_for_user.return_value = 5
        mock_coaching_session_repo.get_monthly_revenue_by_currency.return_value = {}  # No revenue this month
        mock_coaching_session_repo.get_unique_clients_count_for_user.return_value = 2

        request = DashboardSummaryRequest(user_id=user_id, month="2025-02")

        # Act
        response = dashboard_use_case.execute(request)

        # Assert
        assert response.current_month_revenue_by_currency == {}
        assert isinstance(response.current_month_revenue_by_currency, dict)

    def test_execute_with_past_year_month(
        self,
        dashboard_use_case: DashboardSummaryUseCase,
        mock_coaching_session_repo: Mock,
        mock_session_repo: Mock,
        user_id: UUID,
    ):
        """Test execute with past year and month."""
        # Arrange
        mock_coaching_session_repo.get_total_minutes_for_user.return_value = 2000
        mock_coaching_session_repo.get_monthly_minutes_for_user.return_value = 150
        mock_session_repo.get_completed_count_for_user.return_value = 25
        mock_coaching_session_repo.get_monthly_revenue_by_currency.return_value = {
            "USD": 18000
        }
        mock_coaching_session_repo.get_unique_clients_count_for_user.return_value = 15

        request = DashboardSummaryRequest(user_id=user_id, month="2024-05")

        # Act
        dashboard_use_case.execute(request)

        # Assert - verify 2024 was parsed correctly
        mock_coaching_session_repo.get_monthly_minutes_for_user.assert_called_once_with(
            user_id, 2024, 5
        )
        mock_coaching_session_repo.get_monthly_revenue_by_currency.assert_called_once_with(
            user_id, 2024, 5
        )

    def test_execute_response_data_integrity(
        self,
        dashboard_use_case: DashboardSummaryUseCase,
        mock_coaching_session_repo: Mock,
        mock_session_repo: Mock,
        user_id: UUID,
    ):
        """Test that response data matches repository returns exactly."""
        # Arrange - use specific values to verify data integrity
        expected_total = 1357
        expected_monthly = 246
        expected_transcripts = 13
        expected_revenue = {"USD": 13579, "TWD": 407370}
        expected_clients = 9

        mock_coaching_session_repo.get_total_minutes_for_user.return_value = (
            expected_total
        )
        mock_coaching_session_repo.get_monthly_minutes_for_user.return_value = (
            expected_monthly
        )
        mock_session_repo.get_completed_count_for_user.return_value = (
            expected_transcripts
        )
        mock_coaching_session_repo.get_monthly_revenue_by_currency.return_value = (
            expected_revenue
        )
        mock_coaching_session_repo.get_unique_clients_count_for_user.return_value = (
            expected_clients
        )

        request = DashboardSummaryRequest(user_id=user_id, month="2025-07")

        # Act
        response = dashboard_use_case.execute(request)

        # Assert - exact value matching
        assert response.total_minutes == expected_total
        assert response.current_month_minutes == expected_monthly
        assert response.transcripts_converted_count == expected_transcripts
        assert response.current_month_revenue_by_currency == expected_revenue
        assert response.unique_clients_total == expected_clients
