"""Tests for User model and related functionality."""

import pytest
from sqlalchemy.exc import IntegrityError

from coaching_assistant.models import User
from coaching_assistant.models.user import UserPlan


class TestUserModel:
    """Test User model basic functionality."""

    def test_create_user_with_required_fields(self, db_session):
        """Test creating a user with all required fields."""
        user = User(
            email="testuser@example.com",
            name="Test User",
            google_id="google123456",
            plan=UserPlan.FREE,
        )

        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.email == "testuser@example.com"
        assert user.name == "Test User"
        assert user.google_id == "google123456"
        assert user.plan == UserPlan.FREE
        assert user.usage_minutes == 0  # Default value
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_create_user_with_optional_fields(self, db_session):
        """Test creating a user with optional fields."""
        user = User(
            email="premium@example.com",
            name="Premium User",
            google_id="google789",
            avatar_url="https://example.com/avatar.jpg",
            plan=UserPlan.PRO,
            usage_minutes=120,
        )

        db_session.add(user)
        db_session.commit()

        assert user.avatar_url == "https://example.com/avatar.jpg"
        assert user.plan == UserPlan.PRO
        assert user.usage_minutes == 120

    def test_user_email_unique_constraint(self, db_session, sample_user):
        """Test that email must be unique."""
        duplicate_user = User(
            email=sample_user.email,  # Same email
            name="Another User",
            google_id="different_google_id",
        )

        db_session.add(duplicate_user)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_google_id_unique_constraint(self, db_session, sample_user):
        """Test that google_id must be unique."""
        duplicate_user = User(
            email="different@example.com",
            name="Another User",
            google_id=sample_user.google_id,  # Same google_id
        )

        db_session.add(duplicate_user)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_str_representation(self, sample_user):
        """Test user string representation."""
        expected = f"<User(email={sample_user.email}, plan={sample_user.plan.value})>"
        assert str(sample_user) == expected


class TestUserPlanLimits:
    """Test user plan usage limit functionality."""

    @pytest.mark.parametrize(
        "plan,current_usage,additional,expected",
        [
            (UserPlan.FREE, 0, 30, True),  # Within free limit
            (UserPlan.FREE, 0, 60, True),  # Exactly at free limit
            (UserPlan.FREE, 0, 61, False),  # Over free limit
            (
                UserPlan.FREE,
                30,
                30,
                True,
            ),  # Within free limit with existing usage
            (
                UserPlan.FREE,
                50,
                15,
                False,
            ),  # Over free limit with existing usage
            (UserPlan.PRO, 0, 300, True),  # Within pro limit
            (UserPlan.PRO, 0, 600, True),  # Exactly at pro limit
            (UserPlan.PRO, 0, 601, False),  # Over pro limit
            (
                UserPlan.PRO,
                400,
                200,
                True,
            ),  # Within pro limit with existing usage
            (
                UserPlan.PRO,
                500,
                150,
                False,
            ),  # Over pro limit with existing usage
            (UserPlan.ENTERPRISE, 0, 10000, True),  # Enterprise unlimited
            (
                UserPlan.ENTERPRISE,
                1000,
                50000,
                True,
            ),  # Enterprise unlimited with usage
        ],
    )
    def test_is_usage_within_limit(
        self, db_session, plan, current_usage, additional, expected
    ):
        """Test usage limit checking for different plans."""
        user = User(
            email="test@example.com",
            name="Test User",
            google_id="test123",
            plan=plan,
            usage_minutes=current_usage,
        )

        assert user.is_usage_within_limit(additional) == expected

    def test_can_create_session(self, db_session):
        """Test session creation permission based on usage limits."""
        user = User(
            email="test@example.com",
            name="Test User",
            google_id="test123",
            plan=UserPlan.FREE,
            usage_minutes=45,  # 45 minutes used
        )

        # Can create 10-minute session (total 55 < 60)
        assert user.can_create_session(10) is True

        # Can create 15-minute session (total 60 = 60)
        assert user.can_create_session(15) is True

        # Cannot create 20-minute session (total 65 > 60)
        assert user.can_create_session(20) is False


class TestUserUsageTracking:
    """Test user usage tracking functionality."""

    def test_add_usage(self, db_session):
        """Test adding usage minutes to user."""
        user = User(
            email="test@example.com",
            name="Test User",
            google_id="test123",
            usage_minutes=30,
        )

        user.add_usage(15)
        assert user.usage_minutes == 45

        user.add_usage(5)
        assert user.usage_minutes == 50

    def test_reset_monthly_usage(self, db_session):
        """Test resetting monthly usage counter."""
        user = User(
            email="test@example.com",
            name="Test User",
            google_id="test123",
            usage_minutes=150,
        )

        user.reset_monthly_usage()
        assert user.usage_minutes == 0

    def test_usage_persistence(self, db_session):
        """Test that usage changes persist to database."""
        user = User(
            email="test@example.com",
            name="Test User",
            google_id="test123",
            usage_minutes=0,
        )

        db_session.add(user)
        db_session.commit()

        # Add usage and commit
        user.add_usage(25)
        db_session.commit()

        # Refresh from database
        db_session.refresh(user)
        assert user.usage_minutes == 25


class TestUserRelationships:
    """Test user relationships with other models."""

    def test_user_sessions_relationship(self, db_session, sample_user):
        """Test that user can have multiple sessions."""
        from coaching_assistant.models import Session
        from coaching_assistant.models.session import SessionStatus

        session1 = Session(
            title="Session 1",
            user_id=sample_user.id,
            status=SessionStatus.PENDING,
        )
        session2 = Session(
            title="Session 2",
            user_id=sample_user.id,
            status=SessionStatus.COMPLETED,
        )

        db_session.add_all([session1, session2])
        db_session.commit()

        # Test relationship access
        sessions = sample_user.sessions.all()
        assert len(sessions) == 2
        assert session1 in sessions
        assert session2 in sessions

    def test_user_cascade_delete(self, db_session, sample_user):
        """Test that deleting user cascades to sessions."""
        from coaching_assistant.models import Session
        from coaching_assistant.models.session import SessionStatus

        session = Session(
            title="Test Session",
            user_id=sample_user.id,
            status=SessionStatus.PENDING,
        )

        db_session.add(session)
        db_session.commit()
        session_id = session.id

        # Delete user
        db_session.delete(sample_user)
        db_session.commit()

        # Check that session is deleted
        deleted_session = db_session.query(Session).filter_by(id=session_id).first()
        assert deleted_session is None
