"""Tests for TranscriptSegment and SessionRole models."""

import pytest
from sqlalchemy.exc import IntegrityError
from coaching_assistant.models import TranscriptSegment, SessionRole
from coaching_assistant.models.transcript import SpeakerRole


class TestTranscriptSegmentModel:
    """Test TranscriptSegment model basic functionality."""

    def test_create_segment_with_required_fields(self, db_session, sample_session):
        """Test creating a transcript segment with required fields."""
        segment = TranscriptSegment(
            session_id=sample_session.id,
            speaker_id=1,
            start_seconds=0.0,
            end_seconds=10.5,
            content="Hello, this is a test segment.",
        )

        db_session.add(segment)
        db_session.commit()

        assert segment.id is not None
        assert segment.session_id == sample_session.id
        assert segment.speaker_id == 1
        assert segment.start_seconds == 0.0
        assert segment.end_seconds == 10.5
        assert segment.content == "Hello, this is a test segment."
        assert segment.created_at is not None
        assert segment.updated_at is not None

    def test_create_segment_with_optional_fields(self, db_session, sample_session):
        """Test creating a transcript segment with optional fields."""
        segment = TranscriptSegment(
            session_id=sample_session.id,
            speaker_id=2,
            start_seconds=10.5,
            end_seconds=25.8,
            content="This segment has confidence score.",
            confidence=0.95,
        )

        db_session.add(segment)
        db_session.commit()

        assert segment.confidence == 0.95

    def test_segment_str_representation(self, db_session, sample_session):
        """Test segment string representation."""
        segment = TranscriptSegment(
            session_id=sample_session.id,
            speaker_id=1,
            start_seconds=5.0,
            end_seconds=15.0,
            content="Test content",
        )

        expected = f"<TranscriptSegment(speaker_id=1, start=5.0s)>"
        assert str(segment) == expected

    def test_segment_session_foreign_key_constraint(self, db_session):
        """Test that segment requires valid session_id."""
        import uuid

        invalid_session_id = uuid.uuid4()

        segment = TranscriptSegment(
            session_id=invalid_session_id,
            speaker_id=1,
            start_seconds=0.0,
            end_seconds=10.0,
            content="Invalid segment",
        )

        db_session.add(segment)

        with pytest.raises(IntegrityError):
            db_session.commit()


class TestTranscriptSegmentProperties:
    """Test TranscriptSegment property methods."""

    @pytest.mark.parametrize(
        "start_seconds,end_seconds,expected_duration",
        [
            (0.0, 10.0, 10.0),
            (5.5, 15.8, 10.3),
            (100.0, 123.45, 23.45),
            (0.0, 0.5, 0.5),
        ],
    )
    def test_duration_sec_property(
        self, db_session, sample_session, start_seconds, end_seconds, expected_duration
    ):
        """Test duration_sec property calculation."""
        segment = TranscriptSegment(
            session_id=sample_session.id,
            speaker_id=1,
            start_seconds=start_seconds,
            end_seconds=end_seconds,
            content="Test content",
        )

        assert (
            abs(segment.duration_sec - expected_duration) < 0.01
        )  # Allow small floating point errors

    @pytest.mark.parametrize(
        "start_seconds,end_seconds,expected_timespan",
        [
            (0.0, 10.0, "00:00 - 00:10"),
            (65.0, 125.0, "01:05 - 02:05"),
            (3661.0, 3721.0, "61:01 - 62:01"),  # Over 60 minutes
            (5.5, 15.8, "00:05 - 00:15"),  # Fractional seconds rounded down
        ],
    )
    def test_formatted_timespan_property(
        self, db_session, sample_session, start_seconds, end_seconds, expected_timespan
    ):
        """Test formatted_timespan property."""
        segment = TranscriptSegment(
            session_id=sample_session.id,
            speaker_id=1,
            start_seconds=start_seconds,
            end_seconds=end_seconds,
            content="Test content",
        )

        assert segment.formatted_timespan == expected_timespan

    def test_get_role_label_default(self, db_session, sample_session):
        """Test get_role_label method returns default label."""
        segment = TranscriptSegment(
            session_id=sample_session.id,
            speaker_id=3,
            start_seconds=0.0,
            end_seconds=10.0,
            content="Test content",
        )

        assert segment.get_role_label() == "Speaker 3"


class TestTranscriptSegmentRelationships:
    """Test TranscriptSegment relationships."""

    def test_segment_session_relationship(self, db_session, sample_session):
        """Test segment-session relationship."""
        segment = TranscriptSegment(
            session_id=sample_session.id,
            speaker_id=1,
            start_seconds=0.0,
            end_seconds=10.0,
            content="Test relationship",
        )

        db_session.add(segment)
        db_session.commit()

        # Test forward relationship
        assert segment.session == sample_session

        # Test reverse relationship
        assert segment in sample_session.segments.all()


class TestSessionRoleModel:
    """Test SessionRole model basic functionality."""

    def test_create_role_with_required_fields(self, db_session, sample_session):
        """Test creating a session role with required fields."""
        role = SessionRole(
            session_id=sample_session.id, speaker_id=1, role=SpeakerRole.COACH
        )

        db_session.add(role)
        db_session.commit()

        assert role.id is not None
        assert role.session_id == sample_session.id
        assert role.speaker_id == 1
        assert role.role == SpeakerRole.COACH
        assert role.created_at is not None
        assert role.updated_at is not None

    def test_role_str_representation(self, db_session, sample_session):
        """Test role string representation."""
        role = SessionRole(
            session_id=sample_session.id, speaker_id=2, role=SpeakerRole.CLIENT
        )

        expected = f"<SessionRole(speaker_id=2, role=client)>"
        assert str(role) == expected

    def test_role_session_foreign_key_constraint(self, db_session):
        """Test that role requires valid session_id."""
        import uuid

        invalid_session_id = uuid.uuid4()

        role = SessionRole(
            session_id=invalid_session_id, speaker_id=1, role=SpeakerRole.COACH
        )

        db_session.add(role)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_unique_session_speaker_constraint(self, db_session, sample_session):
        """Test that speaker_id must be unique within a session."""
        role1 = SessionRole(
            session_id=sample_session.id, speaker_id=1, role=SpeakerRole.COACH
        )
        role2 = SessionRole(
            session_id=sample_session.id,
            speaker_id=1,  # Same speaker_id in same session
            role=SpeakerRole.CLIENT,
        )

        db_session.add(role1)
        db_session.commit()  # First role should work

        db_session.add(role2)

        with pytest.raises(IntegrityError):
            db_session.commit()  # Second role should fail

    def test_different_sessions_same_speaker_allowed(self, db_session, sample_user):
        """Test that same speaker_id is allowed in different sessions."""
        from coaching_assistant.models import Session
        from coaching_assistant.models.session import SessionStatus

        # Create first session
        session1 = Session(
            title="First Session", user_id=sample_user.id, status=SessionStatus.PENDING
        )
        # Create second session
        session2 = Session(
            title="Second Session", user_id=sample_user.id, status=SessionStatus.PENDING
        )
        db_session.add_all([session1, session2])
        db_session.commit()

        # Create roles with same speaker_id in different sessions
        role1 = SessionRole(
            session_id=session1.id, speaker_id=1, role=SpeakerRole.COACH
        )
        role2 = SessionRole(
            session_id=session2.id,
            speaker_id=1,  # Same speaker_id but different session
            role=SpeakerRole.CLIENT,
        )

        db_session.add_all([role1, role2])
        db_session.commit()  # Should work fine

        assert role1.speaker_id == role2.speaker_id
        assert role1.session_id != role2.session_id


class TestSpeakerRoleEnum:
    """Test SpeakerRole enum functionality."""

    @pytest.mark.parametrize(
        "role,expected_value",
        [
            (SpeakerRole.COACH, "coach"),
            (SpeakerRole.CLIENT, "client"),
            (SpeakerRole.UNKNOWN, "unknown"),
        ],
    )
    def test_speaker_role_values(self, role, expected_value):
        """Test SpeakerRole enum values."""
        assert role.value == expected_value


class TestSessionRoleMethods:
    """Test SessionRole class methods."""

    def test_create_assignment_class_method(self, sample_session):
        """Test create_assignment class method."""
        role = SessionRole.create_assignment(
            session_id=sample_session.id, speaker_id=2, role=SpeakerRole.CLIENT
        )

        assert role.session_id == sample_session.id
        assert role.speaker_id == 2
        assert role.role == SpeakerRole.CLIENT
        assert role.id is None  # Not yet committed to database


class TestSessionRoleRelationships:
    """Test SessionRole relationships."""

    def test_role_session_relationship(self, db_session, sample_session):
        """Test role-session relationship."""
        role = SessionRole(
            session_id=sample_session.id, speaker_id=1, role=SpeakerRole.COACH
        )

        db_session.add(role)
        db_session.commit()

        # Test forward relationship
        assert role.session == sample_session

        # Test reverse relationship
        assert role in sample_session.roles


class TestIntegratedTranscriptFunctionality:
    """Test integrated functionality between transcript models."""

    def test_session_get_speaker_role_integration(self, db_session, sample_session):
        """Test Session.get_speaker_role with actual SessionRole data."""
        # Create role assignment
        role = SessionRole(
            session_id=sample_session.id, speaker_id=1, role=SpeakerRole.COACH
        )
        db_session.add(role)
        db_session.commit()

        # Test that session can resolve speaker role
        assert sample_session.get_speaker_role(1) == "coach"
        assert sample_session.get_speaker_role(2) == "Speaker 2"  # No role assigned

    def test_complete_session_data_flow(self, db_session, sample_session):
        """Test complete data flow: Session → Segments → Roles."""
        # Create transcript segments
        segments = [
            TranscriptSegment(
                session_id=sample_session.id,
                speaker_id=1,
                start_seconds=0.0,
                end_seconds=10.0,
                content="Hello, I'm the coach.",
                confidence=0.95,
            ),
            TranscriptSegment(
                session_id=sample_session.id,
                speaker_id=2,
                start_seconds=10.0,
                end_seconds=20.0,
                content="Hi, I'm the client.",
                confidence=0.92,
            ),
            TranscriptSegment(
                session_id=sample_session.id,
                speaker_id=1,
                start_seconds=20.0,
                end_seconds=30.0,
                content="How are you feeling today?",
                confidence=0.88,
            ),
        ]

        # Create role assignments
        roles = [
            SessionRole(
                session_id=sample_session.id, speaker_id=1, role=SpeakerRole.COACH
            ),
            SessionRole(
                session_id=sample_session.id, speaker_id=2, role=SpeakerRole.CLIENT
            ),
        ]

        db_session.add_all(segments + roles)
        db_session.commit()

        # Test complete integration
        assert sample_session.segments_count == 3
        assert len(sample_session.roles) == 2

        # Test speaker role resolution
        assert sample_session.get_speaker_role(1) == "coach"
        assert sample_session.get_speaker_role(2) == "client"

        # Test segment ordering (should be ordered by start_seconds)
        session_segments = sample_session.segments.all()
        for i in range(len(session_segments) - 1):
            assert (
                session_segments[i].start_seconds
                <= session_segments[i + 1].start_seconds
            )

        # Test total duration calculation
        total_duration = sum(seg.duration_sec for seg in session_segments)
        assert total_duration == 30.0  # 3 segments of 10 seconds each
