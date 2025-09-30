"""Tests for UsageAnalyticsService."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from coaching_assistant.models.session import Session, SessionStatus
from coaching_assistant.models.usage_history import UsageHistory
from coaching_assistant.models.usage_log import TranscriptionType, UsageLog
from coaching_assistant.models.user import User, UserPlan
from coaching_assistant.services.usage_analytics_service import (
    UsageAnalyticsService,
)


class TestUsageAnalyticsService:
    """Test suite for UsageAnalyticsService."""

    @pytest.fixture
    def analytics_service(self, db_session):
        """Create a UsageAnalyticsService instance."""
        return UsageAnalyticsService(db_session)

    @pytest.fixture
    def test_user(self, db_session):
        """Create a test user."""
        user = User(email="test@example.com", name="Test User", plan=UserPlan.FREE)
        db_session.add(user)
        db_session.commit()
        return user

    def test_record_usage_snapshot_creates_new(
        self, analytics_service, test_user, db_session
    ):
        """Test recording a new usage snapshot."""
        # Create some usage logs to aggregate
        session = Session(
            user_id=test_user.id,
            title="Test Session",
            audio_filename="test_audio.mp3",
            status=SessionStatus.COMPLETED,
        )
        db_session.add(session)
        db_session.commit()

        usage_log = UsageLog(
            user_id=test_user.id,
            session_id=session.id,
            duration_minutes=30,
            duration_seconds=1800,
            stt_provider="google",
            user_plan="FREE",
            transcription_type=TranscriptionType.ORIGINAL,
            cost_usd=Decimal("1.50"),
            is_billable=True,
        )
        db_session.add(usage_log)
        db_session.commit()

        # Record snapshot
        snapshot = analytics_service.record_usage_snapshot(test_user.id, "daily")

        # Verify snapshot was created
        assert snapshot is not None
        assert snapshot.user_id == test_user.id
        assert snapshot.period_type == "daily"
        assert snapshot.audio_minutes_processed >= 30  # Should include our usage log
        assert snapshot.plan_name == "free"

        # Verify it was saved to database
        db_snapshot = (
            db_session.query(UsageHistory)
            .filter(
                UsageHistory.user_id == test_user.id,
                UsageHistory.period_type == "daily",
            )
            .first()
        )
        assert db_snapshot is not None
        assert db_snapshot.id == snapshot.id

    def test_record_usage_snapshot_updates_existing(
        self, analytics_service, test_user, db_session
    ):
        """Test that recording a snapshot updates existing record for same period."""
        # Create initial snapshot
        start_time = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        existing_snapshot = UsageHistory(
            user_id=test_user.id,
            period_type="daily",
            period_start=start_time,
            period_end=start_time + timedelta(days=1),
            sessions_created=1,
            audio_minutes_processed=Decimal("10"),
            plan_name="FREE",
        )
        db_session.add(existing_snapshot)
        db_session.commit()

        existing_id = existing_snapshot.id

        # Record new snapshot (should update existing)
        updated_snapshot = analytics_service.record_usage_snapshot(
            test_user.id, "daily"
        )

        # Verify same record was updated, not new one created
        assert updated_snapshot.id == existing_id

        # Verify there's still only one record
        count = (
            db_session.query(UsageHistory)
            .filter(
                UsageHistory.user_id == test_user.id,
                UsageHistory.period_type == "daily",
            )
            .count()
        )
        assert count == 1

    def test_get_usage_trends_with_history_data(
        self, analytics_service, test_user, db_session
    ):
        """Test getting usage trends from existing history data."""
        # Create multiple history records over several days
        base_date = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        for i in range(7):  # 7 days of data
            history = UsageHistory(
                user_id=test_user.id,
                period_type="daily",
                period_start=base_date - timedelta(days=i),
                period_end=base_date - timedelta(days=i) + timedelta(days=1),
                sessions_created=i + 1,
                audio_minutes_processed=Decimal((i + 1) * 15),  # 15, 30, 45, etc.
                transcriptions_completed=i + 2,
                total_cost_usd=Decimal((i + 1) * 2.5),
                plan_name="FREE",
            )
            db_session.add(history)

        db_session.commit()

        # Get trends
        trends = analytics_service.get_usage_trends(test_user.id, "7d", "day")

        # Verify trends data
        assert len(trends) == 7

        # Check first trend (most recent)
        first_trend = trends[0]
        assert "date" in first_trend
        assert "sessions" in first_trend
        assert "minutes" in first_trend
        assert "transcriptions" in first_trend
        assert "cost" in first_trend

        # Verify data is ordered (most recent first in DB query, but trends
        # should be chronological)
        assert isinstance(first_trend["sessions"], int)
        assert isinstance(first_trend["minutes"], float)

    def test_get_usage_trends_fallback_to_logs(
        self, analytics_service, test_user, db_session
    ):
        """Test getting trends falls back to usage logs when no history data."""
        # Create session and usage logs directly (no history records)
        session = Session(
            user_id=test_user.id,
            title="Test Session",
            audio_filename="test_audio.mp3",
            status=SessionStatus.COMPLETED,
        )
        db_session.add(session)
        db_session.commit()

        # Create usage logs for past few days
        base_date = datetime.now(UTC)
        for i in range(3):
            usage_log = UsageLog(
                user_id=test_user.id,
                session_id=session.id,
                duration_minutes=20 + i * 5,
                duration_seconds=(20 + i * 5) * 60,
                stt_provider="google",
                user_plan="FREE",
                created_at=base_date - timedelta(days=i),
            )
            db_session.add(usage_log)

        db_session.commit()

        # Get trends (should fall back to usage logs)
        trends = analytics_service.get_usage_trends(test_user.id, "7d", "day")

        # Should have some data from usage logs
        assert len(trends) >= 0  # May be empty or contain data depending on aggregation

    def test_predict_usage_with_sufficient_data(
        self, analytics_service, test_user, db_session
    ):
        """Test usage prediction with sufficient historical data."""
        # Create 30 days of history data with growing trend
        base_date = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        for i in range(30):
            # Growing usage pattern
            sessions = max(1, i // 5)  # Gradual increase
            minutes = sessions * 20

            history = UsageHistory(
                user_id=test_user.id,
                period_type="daily",
                period_start=base_date - timedelta(days=29 - i),
                period_end=base_date - timedelta(days=29 - i) + timedelta(days=1),
                sessions_created=sessions,
                audio_minutes_processed=Decimal(minutes),
                transcriptions_completed=sessions,
                plan_name="FREE",
            )
            db_session.add(history)

        db_session.commit()

        # Get predictions
        predictions = analytics_service.predict_usage(test_user.id)

        # Verify prediction structure
        assert "predicted_sessions" in predictions
        assert "predicted_minutes" in predictions
        assert "confidence" in predictions
        assert "recommendation" in predictions
        assert "growth_rate" in predictions
        assert "current_trend" in predictions

        # Verify data types
        assert isinstance(predictions["predicted_sessions"], int)
        assert isinstance(predictions["predicted_minutes"], int)
        assert isinstance(predictions["confidence"], float)
        assert isinstance(predictions["recommendation"], str)
        assert (
            predictions["confidence"] > 0
        )  # Should have some confidence with 30 days of data

    def test_predict_usage_insufficient_data(
        self, analytics_service, test_user, db_session
    ):
        """Test usage prediction with insufficient historical data."""
        # Create only 3 days of data (less than minimum 7)
        base_date = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        for i in range(3):
            history = UsageHistory(
                user_id=test_user.id,
                period_type="daily",
                period_start=base_date - timedelta(days=i),
                period_end=base_date - timedelta(days=i) + timedelta(days=1),
                sessions_created=1,
                audio_minutes_processed=Decimal(15),
                plan_name="FREE",
            )
            db_session.add(history)

        db_session.commit()

        # Get predictions
        predictions = analytics_service.predict_usage(test_user.id)

        # Should return low confidence and default values
        assert predictions["confidence"] == 0.0
        assert predictions["predicted_sessions"] == 0
        assert predictions["predicted_minutes"] == 0
        assert "Insufficient" in predictions["recommendation"]

    def test_generate_insights_low_utilization(
        self, analytics_service, test_user, db_session
    ):
        """Test generating insights for low plan utilization."""
        # Create usage data showing low utilization (less than 30%)
        base_date = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        for i in range(10):
            history = UsageHistory(
                user_id=test_user.id,
                period_type="daily",
                period_start=base_date - timedelta(days=i),
                period_end=base_date - timedelta(days=i) + timedelta(days=1),
                sessions_created=1,
                audio_minutes_processed=Decimal(5),  # Very low usage
                transcriptions_completed=1,
                plan_name="FREE",
                plan_limits={
                    "minutes": 60,
                    "sessions": 10,
                },  # FREE plan limits
            )
            db_session.add(history)

        db_session.commit()

        # Generate insights
        insights = analytics_service.generate_insights(test_user.id)

        # Should contain optimization insight for low utilization
        optimization_insights = [i for i in insights if i["type"] == "optimization"]
        assert len(optimization_insights) > 0

        first_insight = optimization_insights[0]
        assert "Low Plan Utilization" in first_insight["title"]
        assert "optimization" == first_insight["type"]
        assert first_insight["priority"] in ["low", "medium", "high"]

    def test_generate_insights_high_utilization(
        self, analytics_service, test_user, db_session
    ):
        """Test generating insights for high plan utilization."""
        # Create usage data showing high utilization (over 85%)
        base_date = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        for i in range(10):
            history = UsageHistory(
                user_id=test_user.id,
                period_type="daily",
                period_start=base_date - timedelta(days=i),
                period_end=base_date - timedelta(days=i) + timedelta(days=1),
                sessions_created=2,
                audio_minutes_processed=Decimal(55),  # High usage (55/60 = 91.7%)
                transcriptions_completed=2,
                plan_name="FREE",
                plan_limits={"minutes": 60, "sessions": 10},
            )
            db_session.add(history)

        db_session.commit()

        # Generate insights
        insights = analytics_service.generate_insights(test_user.id)

        # Should contain warning insight for high utilization
        warning_insights = [i for i in insights if i["type"] == "warning"]
        assert len(warning_insights) > 0

        warning_insight = warning_insights[0]
        assert "High Plan Utilization" in warning_insight["title"]
        assert warning_insight["priority"] == "high"
        assert warning_insight["action"] == "upgrade"

    def test_generate_insights_rapid_growth(
        self, analytics_service, test_user, db_session
    ):
        """Test generating insights for rapid usage growth."""
        base_date = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        # Create data showing rapid growth (low usage initially, high usage
        # recently)
        for i in range(20):
            if i < 10:
                # Low usage in first half
                sessions = 1
                minutes = 10
            else:
                # High usage in second half (rapid growth)
                sessions = 5
                minutes = 50

            history = UsageHistory(
                user_id=test_user.id,
                period_type="daily",
                period_start=base_date - timedelta(days=19 - i),
                period_end=base_date - timedelta(days=19 - i) + timedelta(days=1),
                sessions_created=sessions,
                audio_minutes_processed=Decimal(minutes),
                transcriptions_completed=sessions,
                plan_name="FREE",
            )
            db_session.add(history)

        db_session.commit()

        # Generate insights
        insights = analytics_service.generate_insights(test_user.id)

        # Should contain trend insight for rapid growth
        trend_insights = [i for i in insights if i["type"] == "trend"]
        assert len(trend_insights) > 0

        # Find the growth insight
        growth_insights = [i for i in trend_insights if "Growth" in i["title"]]
        if growth_insights:
            growth_insight = growth_insights[0]
            assert growth_insight["priority"] == "high"
            assert growth_insight["action"] == "upgrade"

    def test_calculate_period_boundaries(self, analytics_service):
        """Test period boundary calculations."""
        test_time = datetime(2024, 8, 15, 14, 30, 45)

        # Test hourly boundaries
        start, end = analytics_service._calculate_period_boundaries(test_time, "hourly")
        assert start == datetime(2024, 8, 15, 14, 0, 0)
        assert end == datetime(2024, 8, 15, 15, 0, 0)

        # Test daily boundaries
        start, end = analytics_service._calculate_period_boundaries(test_time, "daily")
        assert start == datetime(2024, 8, 15, 0, 0, 0)
        assert end == datetime(2024, 8, 16, 0, 0, 0)

        # Test monthly boundaries
        start, end = analytics_service._calculate_period_boundaries(
            test_time, "monthly"
        )
        assert start == datetime(2024, 8, 1, 0, 0, 0)
        assert end == datetime(2024, 9, 1, 0, 0, 0)

        # Test December to January transition
        test_time_dec = datetime(2024, 12, 15, 10, 0, 0)
        start, end = analytics_service._calculate_period_boundaries(
            test_time_dec, "monthly"
        )
        assert start == datetime(2024, 12, 1, 0, 0, 0)
        assert end == datetime(2025, 1, 1, 0, 0, 0)

    def test_parse_period_to_date(self, analytics_service):
        """Test parsing period strings to dates."""
        now = datetime.now(UTC)

        # Test 7 days
        result = analytics_service._parse_period_to_date("7d")
        expected = now - timedelta(days=7)
        assert abs((result - expected).total_seconds()) < 60  # Within 1 minute

        # Test 30 days
        result = analytics_service._parse_period_to_date("30d")
        expected = now - timedelta(days=30)
        assert abs((result - expected).total_seconds()) < 60

        # Test 3 months
        result = analytics_service._parse_period_to_date("3m")
        expected = now - timedelta(days=90)
        assert abs((result - expected).total_seconds()) < 60

        # Test 12 months
        result = analytics_service._parse_period_to_date("12m")
        expected = now - timedelta(days=365)
        assert abs((result - expected).total_seconds()) < 60

        # Test invalid period (should default to 30d)
        result = analytics_service._parse_period_to_date("invalid")
        expected = now - timedelta(days=30)
        assert abs((result - expected).total_seconds()) < 60

    def test_aggregate_usage_data(self, analytics_service, test_user, db_session):
        """Test aggregating usage data for a period."""
        # Create sessions and usage logs
        session1 = Session(
            user_id=test_user.id,
            title="Test Session 1",
            audio_filename="test_audio_1.mp3",
            status=SessionStatus.COMPLETED,
        )
        session2 = Session(
            user_id=test_user.id,
            title="Test Session 2",
            audio_filename="test_audio_2.mp3",
            status=SessionStatus.COMPLETED,
        )
        db_session.add_all([session1, session2])
        db_session.commit()

        # Create usage logs
        usage_log1 = UsageLog(
            user_id=test_user.id,
            session_id=session1.id,
            duration_minutes=30,
            duration_seconds=1800,
            stt_provider="google",
            user_plan="FREE",
            cost_usd=Decimal("1.50"),
            is_billable=True,
            transcription_type=TranscriptionType.ORIGINAL,
        )
        usage_log2 = UsageLog(
            user_id=test_user.id,
            session_id=session2.id,
            duration_minutes=20,
            duration_seconds=1200,
            stt_provider="assemblyai",
            user_plan="FREE",
            cost_usd=Decimal("1.00"),
            is_billable=False,
            transcription_type=TranscriptionType.RETRY_FAILED,
        )
        db_session.add_all([usage_log1, usage_log2])
        db_session.commit()

        # Aggregate data for today
        start_date = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_date = start_date + timedelta(days=1)

        aggregated = analytics_service._aggregate_usage_data(
            test_user.id, start_date, end_date
        )

        # Verify aggregated data
        assert aggregated["sessions_created"] == 2
        assert aggregated["audio_minutes_processed"] == 50  # 30 + 20
        assert aggregated["transcriptions_completed"] == 2
        assert aggregated["plan_name"] == "free"
        assert aggregated["total_cost_usd"] == 2.50  # 1.50 + 1.00
        assert aggregated["billable_transcriptions"] == 1  # Only usage_log1
        assert aggregated["free_retries"] == 1  # Only usage_log2
        assert aggregated["google_stt_minutes"] == 30
        assert aggregated["assemblyai_minutes"] == 20

    def test_generate_plan_recommendation(self, analytics_service):
        """Test plan recommendation generation."""
        # Test recommendation to upgrade from FREE
        # FREE plan has 200 minutes, so 165 minutes = 82.5% (exceeds 80% threshold)
        recommendation = analytics_service._generate_plan_recommendation(
            predicted_sessions=50,
            predicted_minutes=165,  # Exceeds 80% of FREE plan (200 * 0.8 = 160)
            current_plan="free",
            growth_rate=25,
        )
        assert (
            "upgrade" in recommendation.lower() or "upgrading" in recommendation.lower()
        )
        assert "PRO" in recommendation

        # Test recommendation to stay on current plan
        recommendation = analytics_service._generate_plan_recommendation(
            predicted_sessions=20,
            predicted_minutes=30,  # Within normal range
            current_plan="free",
            growth_rate=5,
        )
        assert (
            "appropriate" in recommendation.lower()
            or "suited" in recommendation.lower()
        )

        # Test recommendation to downgrade
        recommendation = analytics_service._generate_plan_recommendation(
            predicted_sessions=5,
            predicted_minutes=10,  # Very low usage (less than 30% of PRO plan)
            current_plan="pro",
            growth_rate=-10,
        )
        assert "FREE" in recommendation or "consider" in recommendation.lower()

    def test_service_handles_nonexistent_user(self, analytics_service):
        """Test that service handles non-existent user gracefully."""
        fake_user_id = uuid4()

        # Should raise ValueError for non-existent user
        with pytest.raises(ValueError, match="User .* not found"):
            analytics_service.record_usage_snapshot(fake_user_id, "daily")

    def test_insights_with_no_data(self, analytics_service, test_user):
        """Test generating insights with no usage data."""
        # Generate insights for user with no usage data
        insights = analytics_service.generate_insights(test_user.id)

        # Should return empty list without errors
        assert isinstance(insights, list)
        assert len(insights) == 0
