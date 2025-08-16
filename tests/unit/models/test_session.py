"""Tests for Session model and related functionality."""

import pytest
from sqlalchemy.exc import IntegrityError
from coaching_assistant.models import Session, User
from coaching_assistant.models.session import SessionStatus
from coaching_assistant.models.user import UserPlan


class TestSessionModel:
    """Test Session model basic functionality."""

    def test_create_session_with_required_fields(self, db_session, sample_user):
        """Test creating a session with all required fields."""
        session = Session(
            title="Test Coaching Session",
            user_id=sample_user.id,
            status=SessionStatus.PENDING,
        )

        db_session.add(session)
        db_session.commit()

        assert session.id is not None
        assert session.title == "Test Coaching Session"
        assert session.user_id == sample_user.id
        assert session.status == SessionStatus.PENDING
        assert session.language == "auto"  # Default value
        assert session.created_at is not None
        assert session.updated_at is not None

    def test_create_session_with_optional_fields(self, db_session, sample_user):
        """Test creating a session with optional fields."""
        session = Session(
            title="Premium Session",
            user_id=sample_user.id,
            audio_filename="premium_audio.mp3",
            duration_seconds=3600,
            language="zh-TW",
            status=SessionStatus.COMPLETED,
            gcs_audio_path="gs://bucket/audio.mp3",
            transcription_job_id="job_123",
            stt_cost_usd="0.05",
        )

        db_session.add(session)
        db_session.commit()

        assert session.audio_filename == "premium_audio.mp3"
        assert session.duration_seconds == 3600
        assert session.language == "zh-TW"
        assert session.status == SessionStatus.COMPLETED
        assert session.gcs_audio_path == "gs://bucket/audio.mp3"
        assert session.transcription_job_id == "job_123"
        assert session.stt_cost_usd == "0.05"

    def test_session_str_representation(self, sample_session):
        """Test session string representation."""
        expected = f"<Session(title={sample_session.title}, status={sample_session.status.value})>"
        assert str(sample_session) == expected

    def test_session_user_foreign_key_constraint(self, db_session):
        """Test that session requires valid user_id."""
        import uuid

        invalid_user_id = uuid.uuid4()

        session = Session(
            title="Invalid Session",
            user_id=invalid_user_id,
            status=SessionStatus.PENDING,
        )

        db_session.add(session)

        with pytest.raises(IntegrityError):
            db_session.commit()


class TestSessionStatus:
    """Test SessionStatus enum functionality."""

    @pytest.mark.parametrize(
        "status,expected_value",
        [
            (SessionStatus.UPLOADING, "uploading"),
            (SessionStatus.PENDING, "pending"),
            (SessionStatus.PROCESSING, "processing"),
            (SessionStatus.COMPLETED, "completed"),
            (SessionStatus.FAILED, "failed"),
            (SessionStatus.CANCELLED, "cancelled"),
        ],
    )
    def test_session_status_values(self, status, expected_value):
        """Test SessionStatus enum values."""
        assert status.value == expected_value


class TestSessionProperties:
    """Test Session property methods."""

    @pytest.mark.parametrize(
        "duration_seconds,expected_minutes",
        [
            (0, 0.0),
            (60, 1.0),
            (90, 1.5),
            (3600, 60.0),
            (None, 0.0),  # Handle None case
        ],
    )
    def test_duration_minutes_property(
        self, db_session, sample_user, duration_seconds, expected_minutes
    ):
        """Test duration_minutes property calculation."""
        session = Session(
            title="Test Session",
            user_id=sample_user.id,
            duration_seconds=duration_seconds,
        )

        assert session.duration_minutes == expected_minutes

    @pytest.mark.parametrize(
        "status,expected",
        [
            (SessionStatus.UPLOADING, False),
            (SessionStatus.PENDING, False),
            (SessionStatus.PROCESSING, False),
            (SessionStatus.COMPLETED, True),
            (SessionStatus.FAILED, True),
            (SessionStatus.CANCELLED, True),
        ],
    )
    def test_is_processing_complete_property(
        self, db_session, sample_user, status, expected
    ):
        """Test is_processing_complete property."""
        session = Session(title="Test Session", user_id=sample_user.id, status=status)

        assert session.is_processing_complete == expected

    def test_segments_count_property(self, db_session, sample_session):
        """Test segments_count property."""
        from coaching_assistant.models import TranscriptSegment

        # Initially no segments
        assert sample_session.segments_count == 0

        # Add some segments
        segment1 = TranscriptSegment(
            session_id=sample_session.id,
            speaker_id=1,
            start_seconds=0.0,
            end_seconds=10.0,
            content="Hello",
        )
        segment2 = TranscriptSegment(
            session_id=sample_session.id,
            speaker_id=2,
            start_seconds=10.0,
            end_seconds=20.0,
            content="World",
        )

        db_session.add_all([segment1, segment2])
        db_session.commit()

        assert sample_session.segments_count == 2


class TestSessionMethods:
    """Test Session instance methods."""

    def test_update_status_without_error(self, sample_session):
        """Test update_status method without error message."""
        sample_session.update_status(SessionStatus.PROCESSING)

        assert sample_session.status == SessionStatus.PROCESSING
        assert sample_session.error_message is None

    def test_update_status_with_error(self, sample_session):
        """Test update_status method with error message."""
        error_msg = "STT service unavailable"
        sample_session.update_status(SessionStatus.FAILED, error_msg)

        assert sample_session.status == SessionStatus.FAILED
        assert sample_session.error_message == error_msg

    def test_mark_completed_without_cost(self, sample_session):
        """Test mark_completed method without cost."""
        sample_session.mark_completed(duration_seconds=1800)

        assert sample_session.status == SessionStatus.COMPLETED
        assert sample_session.duration_seconds == 1800
        assert sample_session.stt_cost_usd is None

    def test_mark_completed_with_cost(self, sample_session):
        """Test mark_completed method with cost."""
        sample_session.mark_completed(duration_seconds=1800, cost_usd="0.03")

        assert sample_session.status == SessionStatus.COMPLETED
        assert sample_session.duration_seconds == 1800
        assert sample_session.stt_cost_usd == "0.03"

    def test_mark_failed(self, sample_session):
        """Test mark_failed method."""
        error_msg = "Audio file corrupted"
        sample_session.mark_failed(error_msg)

        assert sample_session.status == SessionStatus.FAILED
        assert sample_session.error_message == error_msg

    def test_get_speaker_role_with_assigned_role(self, db_session, sample_session):
        """Test get_speaker_role method with assigned role."""
        from coaching_assistant.models import SessionRole
        from coaching_assistant.models.transcript import SpeakerRole

        # Create role assignment
        role = SessionRole(
            session_id=sample_session.id, speaker_id=1, role=SpeakerRole.COACH
        )
        db_session.add(role)
        db_session.commit()

        assert sample_session.get_speaker_role(1) == "coach"

    def test_get_speaker_role_without_assigned_role(self, sample_session):
        """Test get_speaker_role method without assigned role."""
        assert sample_session.get_speaker_role(1) == "Speaker 1"
        assert sample_session.get_speaker_role(2) == "Speaker 2"


class TestSessionRelationships:
    """Test Session relationships with other models."""

    def test_session_user_relationship(self, db_session, sample_user):
        """Test session-user relationship."""
        session = Session(
            title="Relationship Test",
            user_id=sample_user.id,
            status=SessionStatus.PENDING,
        )

        db_session.add(session)
        db_session.commit()

        # Test forward relationship
        assert session.user == sample_user

        # Test reverse relationship
        assert session in sample_user.sessions.all()

    def test_session_segments_relationship(self, db_session, sample_session):
        """Test session-segments relationship."""
        from coaching_assistant.models import TranscriptSegment

        segment1 = TranscriptSegment(
            session_id=sample_session.id,
            speaker_id=1,
            start_seconds=0.0,
            end_seconds=10.0,
            content="First segment",
        )
        segment2 = TranscriptSegment(
            session_id=sample_session.id,
            speaker_id=2,
            start_seconds=10.0,
            end_seconds=20.0,
            content="Second segment",
        )

        db_session.add_all([segment1, segment2])
        db_session.commit()

        # Test relationship and ordering
        segments = sample_session.segments.all()
        assert len(segments) == 2
        assert (
            segments[0].start_seconds <= segments[1].start_seconds
        )  # Ordered by start_seconds

    def test_session_roles_relationship(self, db_session, sample_session):
        """Test session-roles relationship."""
        from coaching_assistant.models import SessionRole
        from coaching_assistant.models.transcript import SpeakerRole

        role1 = SessionRole(
            session_id=sample_session.id, speaker_id=1, role=SpeakerRole.COACH
        )
        role2 = SessionRole(
            session_id=sample_session.id, speaker_id=2, role=SpeakerRole.CLIENT
        )

        db_session.add_all([role1, role2])
        db_session.commit()

        # Test relationship
        roles = sample_session.roles
        assert len(roles) == 2
        assert role1 in roles
        assert role2 in roles

    def test_session_cascade_delete(self, db_session, sample_session):
        """Test that deleting session cascades to segments and roles."""
        from coaching_assistant.models import TranscriptSegment, SessionRole
        from coaching_assistant.models.transcript import SpeakerRole

        # Create segment and role
        segment = TranscriptSegment(
            session_id=sample_session.id,
            speaker_id=1,
            start_seconds=0.0,
            end_seconds=10.0,
            content="Test segment",
        )
        role = SessionRole(
            session_id=sample_session.id, speaker_id=1, role=SpeakerRole.COACH
        )

        db_session.add_all([segment, role])
        db_session.commit()

        segment_id = segment.id
        role_id = role.id

        # Delete session
        db_session.delete(sample_session)
        db_session.commit()

        # Check that segment and role are deleted
        deleted_segment = (
            db_session.query(TranscriptSegment).filter_by(id=segment_id).first()
        )
        deleted_role = db_session.query(SessionRole).filter_by(id=role_id).first()

        assert deleted_segment is None
        assert deleted_role is None
