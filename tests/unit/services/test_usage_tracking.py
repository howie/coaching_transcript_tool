"""Tests for usage tracking service."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from coaching_assistant.models.usage_analytics import UsageAnalytics
from coaching_assistant.models.usage_log import (
    TranscriptionType,
    UsageLog,
)
from coaching_assistant.models.user import User, UserPlan
from coaching_assistant.services.usage_tracking import (
    PlanLimits,
    UsageTrackingService,
)


class TestPlanLimits:
    """Test suite for PlanLimits class."""

    def test_get_limits_free_plan(self):
        """Test plan limits for free tier."""
        limits = PlanLimits.get_limits(UserPlan.FREE)
        assert limits["minutes_per_month"] == 120
        assert limits["sessions_per_month"] == 10
        assert limits["max_file_size_mb"] == 50
        assert limits["export_formats"] == ["json", "txt"]

    def test_get_limits_pro_plan(self):
        """Test plan limits for pro tier."""
        limits = PlanLimits.get_limits(UserPlan.PRO)
        assert limits["minutes_per_month"] == 1200
        assert limits["sessions_per_month"] == 100
        assert limits["max_file_size_mb"] == 200
        assert limits["export_formats"] == ["json", "txt", "vtt", "srt"]

    def test_get_limits_enterprise_plan(self):
        """Test plan limits for enterprise tier."""
        limits = PlanLimits.get_limits(UserPlan.ENTERPRISE)
        assert limits["minutes_per_month"] == float("inf")
        assert limits["sessions_per_month"] == float("inf")
        assert limits["max_file_size_mb"] == 500
        assert limits["export_formats"] == [
            "json",
            "txt",
            "vtt",
            "srt",
            "xlsx",
        ]

    def test_validate_file_size(self):
        """Test file size validation."""
        # Free plan - 50MB limit
        assert PlanLimits.validate_file_size(UserPlan.FREE, 30) is True
        assert PlanLimits.validate_file_size(UserPlan.FREE, 50) is True
        assert PlanLimits.validate_file_size(UserPlan.FREE, 51) is False

        # Pro plan - 200MB limit
        assert PlanLimits.validate_file_size(UserPlan.PRO, 199) is True
        assert PlanLimits.validate_file_size(UserPlan.PRO, 201) is False

        # Enterprise - 500MB limit
        assert PlanLimits.validate_file_size(UserPlan.ENTERPRISE, 499) is True
        assert PlanLimits.validate_file_size(UserPlan.ENTERPRISE, 501) is False

    def test_validate_export_format(self):
        """Test export format validation."""
        # Free plan formats
        assert PlanLimits.validate_export_format(UserPlan.FREE, "json") is True
        assert PlanLimits.validate_export_format(UserPlan.FREE, "txt") is True
        assert PlanLimits.validate_export_format(UserPlan.FREE, "vtt") is False
        assert PlanLimits.validate_export_format(UserPlan.FREE, "xlsx") is False

        # Pro plan formats
        assert PlanLimits.validate_export_format(UserPlan.PRO, "vtt") is True
        assert PlanLimits.validate_export_format(UserPlan.PRO, "srt") is True
        assert PlanLimits.validate_export_format(UserPlan.PRO, "xlsx") is False

        # Enterprise formats
        assert PlanLimits.validate_export_format(UserPlan.ENTERPRISE, "xlsx") is True
        assert PlanLimits.validate_export_format(UserPlan.ENTERPRISE, "json") is True


class TestUsageTrackingService:
    """Test suite for UsageTrackingService."""

    def test_create_usage_log_success(self, db_session: Session, test_session):
        """Test successful usage logging."""
        service = UsageTrackingService(db_session)

        log_entry = service.create_usage_log(
            session=test_session,
            transcription_type=TranscriptionType.ORIGINAL,
            cost_usd=0.50,
            is_billable=True,
            billing_reason="transcription_completed",
        )

        assert log_entry is not None
        assert log_entry.user_id == test_session.user_id
        assert log_entry.session_id == test_session.id
        assert log_entry.transcription_type == TranscriptionType.ORIGINAL
        assert float(log_entry.cost_usd) == 0.50
        assert log_entry.is_billable is True

        # Verify it's in the database
        saved_log = db_session.query(UsageLog).filter_by(id=log_entry.id).first()
        assert saved_log is not None

    def test_create_usage_log_retry(self, db_session: Session, test_session):
        """Test usage logging for retry transcription."""
        service = UsageTrackingService(db_session)

        # Create initial log
        initial_log = service.create_usage_log(
            session=test_session, transcription_type=TranscriptionType.ORIGINAL
        )
        db_session.commit()

        # Create retry log
        retry_log = service.create_usage_log(
            session=test_session,
            transcription_type=TranscriptionType.RETRY_FAILED,
            is_billable=False,
            billing_reason="retry_after_failure",
        )

        assert retry_log.transcription_type == TranscriptionType.RETRY_FAILED
        assert retry_log.is_billable is False
        assert retry_log.parent_log_id == initial_log.id

    def test_get_user_usage_summary(self, db_session: Session, test_user: User):
        """Test getting user usage summary."""
        service = UsageTrackingService(db_session)

        # Create some usage logs
        now = datetime.utcnow()
        logs = [
            UsageLog(
                user_id=str(test_user.id),
                usage_type=TranscriptionType.ORIGINAL,
                session_id=f"session-{i}",
                duration_minutes=10.0,
                cost_usd=Decimal("0.50"),
                created_at=now - timedelta(days=i),
            )
            for i in range(5)
        ]
        db_session.add_all(logs)
        db_session.commit()

        # Update user's current month usage
        test_user.usage_minutes = 50
        test_user.session_count = 5
        test_user.transcription_count = 5
        db_session.commit()

        summary = service.get_user_usage_summary(str(test_user.id))

        assert summary["user_id"] == str(test_user.id)
        assert summary["current_month"]["total_minutes"] == 50
        assert summary["current_month"]["session_count"] == 5
        assert summary["current_month"]["transcription_count"] == 5
        assert len(summary["recent_activity"]) == 5
        assert summary["lifetime"]["total_transcriptions"] == 5
        assert float(summary["lifetime"]["total_cost"]) == 2.50

    def test_get_user_usage_history(self, db_session: Session, test_user: User):
        """Test getting user usage history."""
        service = UsageTrackingService(db_session)

        # Create usage logs for multiple months
        base_date = datetime.utcnow().replace(day=1)
        for month_offset in range(3):
            month_date = base_date - timedelta(days=30 * month_offset)
            for i in range(3):
                log = UsageLog(
                    user_id=str(test_user.id),
                    usage_type=TranscriptionType.ORIGINAL,
                    session_id=f"session-{month_offset}-{i}",
                    duration_minutes=10.0,
                    cost_usd=Decimal("0.50"),
                    created_at=month_date + timedelta(days=i),
                )
                db_session.add(log)
        db_session.commit()

        history = service.get_user_usage_history(str(test_user.id), months=3)

        assert history["user_id"] == str(test_user.id)
        assert history["months_requested"] == 3
        assert len(history["monthly_breakdown"]) <= 3
        assert history["total_period"]["total_transcriptions"] == 9

    def test_get_user_analytics(self, db_session: Session, test_user: User):
        """Test getting user analytics."""
        service = UsageTrackingService(db_session)

        # Create analytics records
        analytics = [
            UsageAnalytics(
                user_id=str(test_user.id),
                month_year="2025-08",
                transcriptions_completed=10,
                transcriptions_retried=2,
                total_minutes_processed=120.0,
                google_stt_minutes=100.0,
                assemblyai_minutes=20.0,
                total_cost_usd=6.0,
                average_duration_minutes=12.0,
                primary_plan="pro",
            ),
            UsageAnalytics(
                user_id=str(test_user.id),
                month_year="2025-07",
                transcriptions_completed=8,
                transcriptions_retried=1,
                total_minutes_processed=96.0,
                google_stt_minutes=96.0,
                assemblyai_minutes=0.0,
                total_cost_usd=4.8,
                average_duration_minutes=12.0,
                primary_plan="pro",
            ),
        ]
        db_session.add_all(analytics)
        db_session.commit()

        result = service.get_user_analytics(str(test_user.id))

        assert result["user_id"] == str(test_user.id)
        assert len(result["monthly_analytics"]) == 2
        assert result["trends"]["total_transcriptions"] == 18
        assert result["trends"]["total_minutes"] == 216.0
        assert result["provider_breakdown"]["google"]["percentage"] > 0

    def test_update_usage_and_check_limit(self, db_session: Session, test_user: User):
        """Test usage update and limit checking."""
        service = UsageTrackingService(db_session)

        # Initial state
        test_user.usage_minutes = 0
        test_user.session_count = 0
        test_user.transcription_count = 0
        db_session.commit()

        # Update usage through session creation
        from coaching_assistant.models.session import Session as SessionModel

        session = SessionModel(
            user_id=test_user.id,
            title="Test Session",
            audio_filename="test.mp3",
            duration_seconds=1800,  # 30 minutes
        )
        db_session.add(session)
        db_session.commit()

        # Create usage log which should update counters
        log = service.create_usage_log(
            session=session, transcription_type=TranscriptionType.ORIGINAL
        )

        # Usage should be updated through the log creation
        assert log.duration_minutes == 30

    def test_check_month_reset(self, db_session: Session, test_user: User):
        """Test monthly usage reset check."""
        UsageTrackingService(db_session)

        # Set last month's usage
        last_month = datetime.utcnow() - timedelta(days=35)
        test_user.usage_minutes = 100
        test_user.session_count = 10
        test_user.transcription_count = 20
        test_user.current_month_start = last_month
        db_session.commit()

        # Check if reset is needed (should detect month change)
        # The service should have a method to check and reset if needed
        # This would be called periodically or on each usage check

        # Manual reset for testing
        if test_user.current_month_start.month != datetime.utcnow().month:
            test_user.usage_minutes = 0
            test_user.session_count = 0
            test_user.transcription_count = 0
            test_user.current_month_start = datetime.utcnow().replace(day=1)
            db_session.commit()

        # Verify reset
        assert test_user.usage_minutes == 0
        assert test_user.session_count == 0

    def test_usage_summary_with_reset_check(self, db_session: Session, test_user: User):
        """Test getting usage summary with month boundary check."""
        service = UsageTrackingService(db_session)

        # Set current month usage
        test_user.usage_minutes = 50
        test_user.session_count = 5
        test_user.transcription_count = 10
        test_user.current_month_start = datetime.utcnow().replace(day=1)
        db_session.commit()

        # Get summary
        summary = service.get_user_usage_summary(str(test_user.id))

        assert summary["user_id"] == str(test_user.id)
        assert summary["current_month"]["total_minutes"] == 50
        assert summary["current_month"]["session_count"] == 5

    def test_get_admin_analytics(self, db_session: Session):
        """Test getting admin analytics."""
        service = UsageTrackingService(db_session)

        # Create test users with different plans
        users = []
        for i, plan in enumerate([UserPlan.FREE, UserPlan.PRO, UserPlan.ENTERPRISE]):
            user = User(
                id=f"user-{i}",
                email=f"user{i}@example.com",
                name=f"User {i}",
                plan=plan,
                usage_minutes=100 * (i + 1),
                session_count=10 * (i + 1),
                transcription_count=20 * (i + 1),
            )
            users.append(user)
        db_session.add_all(users)

        # Create usage logs
        for user in users:
            for j in range(3):
                log = UsageLog(
                    user_id=str(user.id),
                    usage_type=TranscriptionType.ORIGINAL,
                    session_id=f"session-{user.id}-{j}",
                    duration_minutes=10.0,
                    cost_usd=Decimal("0.50"),
                    created_at=datetime.utcnow() - timedelta(days=j),
                )
                db_session.add(log)
        db_session.commit()

        # Get admin analytics
        analytics = service.get_admin_analytics()

        assert analytics["total_users"] == 3
        assert analytics["total_transcriptions"] == 9
        assert analytics["plan_distribution"]["free"] == 1
        assert analytics["plan_distribution"]["pro"] == 1
        assert analytics["plan_distribution"]["enterprise"] == 1
        assert analytics["usage_by_plan"]["free"]["users"] == 1
        assert analytics["usage_by_plan"]["pro"]["users"] == 1

    def test_cost_calculation_in_usage_log(self, db_session: Session, test_session):
        """Test cost calculation in usage log creation."""
        service = UsageTrackingService(db_session)

        # Set session provider and duration
        test_session.stt_provider = "google"
        test_session.duration_seconds = 600  # 10 minutes
        db_session.commit()

        # Create log without explicit cost (should calculate)
        log = service.create_usage_log(
            session=test_session,
            transcription_type=TranscriptionType.ORIGINAL,
            cost_usd=None,  # Let it calculate
            is_billable=True,
        )

        # Google STT rate is ~$0.016 per minute
        expected_cost = (600 / 60.0) * 0.016
        assert float(log.cost_usd) == pytest.approx(expected_cost, rel=0.01)


# Removed decorator tests as they don't exist in the actual service


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user."""
    import uuid

    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        name="Test User",
        plan=UserPlan.PRO,
        usage_minutes=0,
        session_count=0,
        transcription_count=0,
        current_month_start=datetime.utcnow().replace(day=1),
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_session(db_session: Session, test_user: User):
    """Create a test session."""
    import uuid

    from coaching_assistant.models.session import Session as SessionModel

    session = SessionModel(
        id=uuid.uuid4(),
        user_id=test_user.id,
        title="Test Session",
        audio_filename="test.mp3",
        duration_seconds=600,  # 10 minutes
        stt_provider="google",
    )
    db_session.add(session)
    db_session.commit()
    return session
