"""Tests for UsageHistory model."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from coaching_assistant.models.usage_history import UsageHistory
from coaching_assistant.models.user import User, UserPlan


class TestUsageHistory:
    """Test suite for UsageHistory model."""

    def test_create_usage_history(self, db_session):
        """Test creating a usage history record."""
        # Create a test user first
        user = User(email="test@example.com", name="Test User", plan=UserPlan.FREE)
        db_session.add(user)
        db_session.commit()

        # Create usage history
        start_time = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_time = start_time + timedelta(days=1)

        usage_history = UsageHistory(
            user_id=user.id,
            period_type="daily",
            period_start=start_time,
            period_end=end_time,
            sessions_created=5,
            audio_minutes_processed=Decimal("120.50"),
            transcriptions_completed=8,
            exports_generated=3,
            plan_name="FREE",
            plan_limits={"minutes": 60, "sessions": 10},
            total_cost_usd=Decimal("5.25"),
        )

        db_session.add(usage_history)
        db_session.commit()

        # Verify the record was created
        assert usage_history.id is not None
        assert usage_history.user_id == user.id
        assert usage_history.period_type == "daily"
        assert usage_history.sessions_created == 5
        assert usage_history.audio_minutes_processed == Decimal("120.50")
        assert usage_history.transcriptions_completed == 8
        assert usage_history.exports_generated == 3
        assert usage_history.plan_name == "FREE"
        assert usage_history.total_cost_usd == Decimal("5.25")

    def test_usage_history_properties(self, db_session):
        """Test calculated properties of UsageHistory."""
        # Create a test user
        user = User(email="test@example.com", name="Test User", plan=UserPlan.PRO)
        db_session.add(user)
        db_session.commit()

        # Create usage history with specific values
        usage_history = UsageHistory(
            user_id=user.id,
            period_type="daily",
            period_start=datetime.now(UTC),
            period_end=datetime.now(UTC) + timedelta(days=1),
            audio_minutes_processed=Decimal("120"),  # 2 hours
            transcriptions_completed=4,
            failed_transcriptions=1,
            plan_limits={"minutes": 600},
            total_cost_usd=Decimal("10.00"),
        )

        # Test total_hours_processed
        assert usage_history.total_hours_processed == 2.0

        # Test avg_session_duration_minutes
        assert (
            usage_history.avg_session_duration_minutes == 30.0
        )  # 120 minutes / 4 transcriptions

        # Test success_rate
        assert usage_history.success_rate == 80.0  # 4 successful / 5 total * 100

        # Test cost_per_minute
        assert usage_history.cost_per_minute == pytest.approx(
            0.0833, rel=1e-3
        )  # $10 / 120 minutes

        # Test utilization_percentage
        assert usage_history.utilization_percentage == 20.0  # 120 / 600 * 100

    def test_usage_history_zero_division_safety(self, db_session):
        """Test that properties handle zero division gracefully."""
        user = User(email="test@example.com", name="Test User", plan=UserPlan.FREE)
        db_session.add(user)
        db_session.commit()

        # Create usage history with zero values
        usage_history = UsageHistory(
            user_id=user.id,
            period_type="daily",
            period_start=datetime.now(UTC),
            period_end=datetime.now(UTC) + timedelta(days=1),
            audio_minutes_processed=Decimal("0"),
            transcriptions_completed=0,
            failed_transcriptions=0,
            plan_limits={},
            total_cost_usd=Decimal("0"),
        )

        # Test that properties return 0 instead of raising division errors
        assert usage_history.avg_session_duration_minutes == 0.0
        assert usage_history.success_rate == 0.0
        assert usage_history.cost_per_minute == 0.0
        assert usage_history.utilization_percentage == 0.0

    def test_usage_history_to_dict(self, db_session):
        """Test converting UsageHistory to dictionary."""
        user = User(email="test@example.com", name="Test User", plan=UserPlan.PRO)
        db_session.add(user)
        db_session.commit()

        start_time = datetime.now(UTC).replace(microsecond=0)
        usage_history = UsageHistory(
            user_id=user.id,
            period_type="daily",
            period_start=start_time,
            period_end=start_time + timedelta(days=1),
            sessions_created=3,
            audio_minutes_processed=Decimal("90"),
            transcriptions_completed=5,
            exports_generated=2,
            plan_name="PRO",
            plan_limits={"minutes": 600, "sessions": 100},
            total_cost_usd=Decimal("7.50"),
            google_stt_minutes=Decimal("60"),
            assemblyai_minutes=Decimal("30"),
            exports_by_format={"pdf": 1, "docx": 1},
        )

        db_session.add(usage_history)
        db_session.commit()

        # Convert to dict
        data = usage_history.to_dict()

        # Verify structure and content
        assert isinstance(data, dict)
        assert data["id"] == str(usage_history.id)
        assert data["user_id"] == str(user.id)
        assert data["period_type"] == "daily"

        # Check usage_metrics
        assert "usage_metrics" in data
        usage_metrics = data["usage_metrics"]
        assert usage_metrics["sessions_created"] == 3
        assert usage_metrics["audio_minutes_processed"] == 90.0
        assert usage_metrics["audio_hours_processed"] == 1.5
        assert usage_metrics["transcriptions_completed"] == 5

        # Check plan_context
        assert "plan_context" in data
        plan_context = data["plan_context"]
        assert plan_context["plan_name"] == "PRO"
        assert plan_context["plan_limits"] == {"minutes": 600, "sessions": 100}

        # Check cost_metrics
        assert "cost_metrics" in data
        cost_metrics = data["cost_metrics"]
        assert cost_metrics["total_cost_usd"] == 7.50

        # Check provider_breakdown
        assert "provider_breakdown" in data
        provider_breakdown = data["provider_breakdown"]
        assert provider_breakdown["google_stt_minutes"] == 60.0
        assert provider_breakdown["assemblyai_minutes"] == 30.0

        # Check export_activity
        assert "export_activity" in data
        export_activity = data["export_activity"]
        assert export_activity["formats"] == {"pdf": 1, "docx": 1}
        assert export_activity["total"] == 2

    def test_create_snapshot_class_method(self, db_session):
        """Test creating UsageHistory using the create_snapshot class method."""
        user = User(email="test@example.com", name="Test User", plan=UserPlan.FREE)
        db_session.add(user)
        db_session.commit()

        # Prepare usage data
        start_time = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_time = start_time + timedelta(days=1)

        usage_data = {
            "sessions_created": 2,
            "audio_minutes_processed": 45,
            "transcriptions_completed": 3,
            "exports_generated": 1,
            "plan_name": "FREE",
            "plan_limits": {"minutes": 60, "sessions": 10},
            "total_cost_usd": 2.25,
            "google_stt_minutes": 30,
            "assemblyai_minutes": 15,
            "exports_by_format": {"pdf": 1},
        }

        # Create snapshot using class method
        snapshot = UsageHistory.create_snapshot(
            user_id=user.id,  # Pass UUID directly
            period_type="daily",
            period_start=start_time,
            period_end=end_time,
            usage_data=usage_data,
        )

        # Verify the snapshot was created correctly
        assert snapshot.user_id == user.id
        assert snapshot.period_type == "daily"
        assert snapshot.period_start == start_time
        assert snapshot.period_end == end_time
        assert snapshot.sessions_created == 2
        assert snapshot.audio_minutes_processed == 45
        assert snapshot.transcriptions_completed == 3
        assert snapshot.exports_generated == 1
        assert snapshot.plan_name == "FREE"
        assert snapshot.plan_limits == {"minutes": 60, "sessions": 10}
        assert snapshot.total_cost_usd == 2.25
        assert snapshot.google_stt_minutes == 30
        assert snapshot.assemblyai_minutes == 15
        assert snapshot.exports_by_format == {"pdf": 1}

    def test_usage_history_unique_constraint(self, db_session):
        """Test that the unique constraint on user_id, period_type, period_start works."""
        user = User(email="test@example.com", name="Test User", plan=UserPlan.FREE)
        db_session.add(user)
        db_session.commit()

        start_time = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_time = start_time + timedelta(days=1)

        # Create first usage history record
        usage_history1 = UsageHistory(
            user_id=user.id,
            period_type="daily",
            period_start=start_time,
            period_end=end_time,
            sessions_created=1,
            plan_name="FREE",
        )
        db_session.add(usage_history1)
        db_session.commit()

        # Try to create a duplicate record (same user, period_type,
        # period_start)
        usage_history2 = UsageHistory(
            user_id=user.id,
            period_type="daily",
            period_start=start_time,  # Same start time
            period_end=end_time,
            sessions_created=2,
            plan_name="FREE",
        )
        db_session.add(usage_history2)

        # Should raise an integrity error due to unique constraint
        with pytest.raises(Exception):  # Could be IntegrityError or similar
            db_session.commit()

    def test_usage_history_relationship_with_user(self, db_session):
        """Test the relationship between UsageHistory and User."""
        user = User(email="test@example.com", name="Test User", plan=UserPlan.PRO)
        db_session.add(user)
        db_session.commit()

        # Create multiple usage history records
        for i in range(3):
            usage_history = UsageHistory(
                user_id=user.id,
                period_type="daily",
                period_start=datetime.now(UTC) + timedelta(days=i),
                period_end=datetime.now(UTC) + timedelta(days=i + 1),
                sessions_created=i + 1,
                plan_name="PRO",
            )
            db_session.add(usage_history)

        db_session.commit()

        # Test the relationship from user to usage_history
        db_session.refresh(user)
        usage_history_records = user.usage_history.all()
        assert len(usage_history_records) == 3

        # Test the relationship from usage_history to user
        first_record = usage_history_records[0]
        assert first_record.user == user
        assert first_record.user.email == "test@example.com"

    def test_usage_history_repr(self, db_session):
        """Test the string representation of UsageHistory."""
        user = User(email="test@example.com", name="Test User", plan=UserPlan.FREE)
        db_session.add(user)
        db_session.commit()

        start_time = datetime.now(UTC)
        usage_history = UsageHistory(
            user_id=user.id,
            period_type="hourly",
            period_start=start_time,
            period_end=start_time + timedelta(hours=1),
            sessions_created=1,
            plan_name="FREE",
        )
        db_session.add(usage_history)
        db_session.commit()

        # Test the repr
        repr_str = repr(usage_history)
        assert "UsageHistory" in repr_str
        assert str(usage_history.id) in repr_str
        assert str(user.id) in repr_str
        assert "hourly" in repr_str
        assert "sessions=1" in repr_str
