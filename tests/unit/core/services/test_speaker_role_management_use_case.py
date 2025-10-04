"""Unit tests for Speaker Role Management Use Cases following TDD methodology.

This module tests the pure business logic of speaker role assignment and retrieval
use cases without any infrastructure dependencies (using mock repositories).

Day 3 additions: Cover missing error paths for 92% → 95%+ coverage.
"""

from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from coaching_assistant.core.models.session import Session, SessionStatus
from coaching_assistant.core.models.transcript import (
    SegmentRole,
    SessionRole,
    SpeakerRole,
)
from coaching_assistant.core.services.speaker_role_management_use_case import (
    SegmentRoleAssignmentUseCase,
    SpeakerRoleAssignmentUseCase,
    SpeakerRoleRetrievalUseCase,
)


class TestSpeakerRoleAssignmentUseCase:
    """Test cases for SpeakerRoleAssignmentUseCase."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session_repo = Mock()
        self.speaker_role_repo = Mock()
        # Updated implementation with speaker role repository
        self.use_case = SpeakerRoleAssignmentUseCase(
            session_repo=self.session_repo,
            speaker_role_repo=self.speaker_role_repo,
        )

        # Common test data
        self.user_id = uuid4()
        self.session_id = uuid4()
        self.session = Session(
            id=self.session_id,
            user_id=self.user_id,
            status=SessionStatus.COMPLETED,
            audio_filename="test.wav",
            duration_seconds=60,
            title="Test Session",
            created_at=datetime.now(UTC),
        )

    def test_execute_successful_assignment(self):
        """Test successful speaker role assignment for completed session."""
        # Arrange
        speaker_roles = {"1": "coach", "2": "client"}
        self.session_repo.get_by_id.return_value = self.session

        # Mock repository save to return the same roles
        mock_saved_roles = [
            SessionRole(
                id=uuid4(),
                session_id=self.session_id,
                speaker_id=1,
                role=SpeakerRole.COACH,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
            SessionRole(
                id=uuid4(),
                session_id=self.session_id,
                speaker_id=2,
                role=SpeakerRole.CLIENT,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
        ]
        self.speaker_role_repo.save_speaker_roles.return_value = mock_saved_roles

        # Act
        result = self.use_case.execute(self.session_id, self.user_id, speaker_roles)

        # Assert - Repository save should be called
        assert result["message"] == "Speaker roles updated successfully"
        assert result["session_id"] == str(self.session_id)
        assert result["speaker_roles"] == speaker_roles
        assert result["assignments_count"] == 2

        # Verify repository was called with correct arguments
        self.speaker_role_repo.save_speaker_roles.assert_called_once()
        call_args = self.speaker_role_repo.save_speaker_roles.call_args
        assert call_args[0][0] == self.session_id  # session_id
        assert len(call_args[0][1]) == 2  # session_roles list

        # Verify the domain objects were created correctly
        saved_session_roles = call_args[0][1]
        assert saved_session_roles[0].speaker_id == 1
        assert saved_session_roles[0].role == SpeakerRole.COACH
        assert saved_session_roles[1].speaker_id == 2
        assert saved_session_roles[1].role == SpeakerRole.CLIENT

    def test_execute_session_not_found(self):
        """Test error handling when session doesn't exist."""
        # Arrange
        speaker_roles = {"1": "coach"}
        self.session_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Session not found"):
            self.use_case.execute(self.session_id, self.user_id, speaker_roles)

    def test_execute_unauthorized_user(self):
        """Test error handling when user doesn't own the session."""
        # Arrange
        wrong_user_id = uuid4()
        speaker_roles = {"1": "coach"}
        self.session_repo.get_by_id.return_value = self.session

        # Act & Assert
        with pytest.raises(
            ValueError, match="Access denied - session not owned by user"
        ):
            self.use_case.execute(self.session_id, wrong_user_id, speaker_roles)

    def test_execute_session_not_completed(self):
        """Test error handling when session is not completed."""
        # Arrange
        processing_session = Session(
            id=self.session_id,
            user_id=self.user_id,
            status=SessionStatus.PROCESSING,
            audio_filename="test.wav",
            duration_seconds=60,
            title="Test Session",
            created_at=datetime.now(UTC),
        )
        speaker_roles = {"1": "coach"}
        self.session_repo.get_by_id.return_value = processing_session

        # Act & Assert
        with pytest.raises(
            ValueError,
            match="Cannot update speaker roles.*Session status: processing",
        ):
            self.use_case.execute(self.session_id, self.user_id, speaker_roles)

    def test_execute_invalid_speaker_id(self):
        """Test error handling for invalid speaker IDs."""
        # Arrange
        self.session_repo.get_by_id.return_value = self.session

        # Test cases for invalid speaker IDs
        invalid_cases = [
            {"abc": "coach"},  # Non-numeric
            {"0": "coach"},  # Zero
            {"-1": "coach"},  # Negative
        ]

        for invalid_speaker_roles in invalid_cases:
            with pytest.raises(ValueError, match="Invalid speaker ID"):
                self.use_case.execute(
                    self.session_id, self.user_id, invalid_speaker_roles
                )

    def test_execute_invalid_role(self):
        """Test error handling for invalid roles."""
        # Arrange
        self.session_repo.get_by_id.return_value = self.session

        # Test cases for invalid roles
        invalid_cases = [
            {"1": "teacher"},  # Wrong role
            {"1": ""},  # Empty role
            {"1": "invalid"},  # Invalid role
        ]

        for invalid_speaker_roles in invalid_cases:
            with pytest.raises(
                ValueError,
                match="Invalid role.*Must be 'coach' or 'client'.*case-insensitive",
            ):
                self.use_case.execute(
                    self.session_id, self.user_id, invalid_speaker_roles
                )

    def test_execute_case_insensitive_roles(self):
        """Test that role validation is case-insensitive."""
        # Arrange
        self.session_repo.get_by_id.return_value = self.session

        # Mock repository save to return the same roles
        mock_saved_roles = [
            SessionRole(
                id=uuid4(),
                session_id=self.session_id,
                speaker_id=1,
                role=SpeakerRole.COACH,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
            SessionRole(
                id=uuid4(),
                session_id=self.session_id,
                speaker_id=2,
                role=SpeakerRole.CLIENT,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
        ]
        self.speaker_role_repo.save_speaker_roles.return_value = mock_saved_roles

        # Test cases for case-insensitive valid roles
        valid_cases = [
            {"1": "coach", "2": "client"},  # lowercase
            {"1": "COACH", "2": "CLIENT"},  # uppercase
            {"1": "Coach", "2": "Client"},  # title case
            {"1": "cOaCh", "2": "cLiEnT"},  # mixed case
        ]

        for speaker_roles in valid_cases:
            # Act - should not raise an exception
            result = self.use_case.execute(self.session_id, self.user_id, speaker_roles)

            # Assert
            assert result["message"] == "Speaker roles updated successfully"
            assert result["session_id"] == str(self.session_id)


class TestSegmentRoleAssignmentUseCase:
    """Test cases for SegmentRoleAssignmentUseCase."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session_repo = Mock()
        self.segment_role_repo = Mock()
        # Updated implementation with segment role repository
        self.use_case = SegmentRoleAssignmentUseCase(
            session_repo=self.session_repo,
            segment_role_repo=self.segment_role_repo,
        )

        # Common test data
        self.user_id = uuid4()
        self.session_id = uuid4()
        self.session = Session(
            id=self.session_id,
            user_id=self.user_id,
            status=SessionStatus.COMPLETED,
            audio_filename="test.wav",
            duration_seconds=60,
            title="Test Session",
            created_at=datetime.now(UTC),
        )

    def test_execute_successful_assignment(self):
        """Test successful segment role assignment for completed session."""
        # Arrange
        segment_id = str(uuid4())
        segment_uuid = UUID(segment_id)
        segment_roles = {segment_id: "coach"}
        self.session_repo.get_by_id.return_value = self.session

        # Mock repository save to return the same roles
        mock_saved_roles = [
            SegmentRole(
                id=uuid4(),
                session_id=self.session_id,
                segment_id=segment_uuid,
                role=SpeakerRole.COACH,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
        ]
        self.segment_role_repo.save_segment_roles.return_value = mock_saved_roles

        # Act
        result = self.use_case.execute(self.session_id, self.user_id, segment_roles)

        # Assert - Repository save should be called
        assert result["message"] == "Segment roles updated successfully"
        assert result["session_id"] == str(self.session_id)
        assert result["segment_roles"] == segment_roles
        assert result["assignments_count"] == 1

        # Verify repository was called with correct arguments
        self.segment_role_repo.save_segment_roles.assert_called_once()
        call_args = self.segment_role_repo.save_segment_roles.call_args
        assert call_args[0][0] == self.session_id  # session_id
        assert len(call_args[0][1]) == 1  # segment_roles list

        # Verify the domain objects were created correctly
        saved_segment_roles = call_args[0][1]
        assert saved_segment_roles[0].segment_id == segment_uuid
        assert saved_segment_roles[0].role == SpeakerRole.COACH

    def test_execute_invalid_segment_id(self):
        """Test error handling for invalid segment IDs."""
        # Arrange
        self.session_repo.get_by_id.return_value = self.session

        # Test invalid UUID format
        invalid_segment_roles = {"not-a-uuid": "coach"}

        with pytest.raises(ValueError, match="Invalid segment ID format"):
            self.use_case.execute(self.session_id, self.user_id, invalid_segment_roles)

    def test_execute_case_insensitive_roles(self):
        """Test that segment role validation is case-insensitive."""
        # Arrange
        segment_id = str(uuid4())
        segment_uuid = UUID(segment_id)
        self.session_repo.get_by_id.return_value = self.session

        # Mock repository save to return the same roles
        mock_saved_roles = [
            SegmentRole(
                id=uuid4(),
                session_id=self.session_id,
                segment_id=segment_uuid,
                role=SpeakerRole.COACH,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
        ]
        self.segment_role_repo.save_segment_roles.return_value = mock_saved_roles

        # Test cases for case-insensitive valid roles
        valid_cases = [
            {segment_id: "coach"},  # lowercase
            {segment_id: "COACH"},  # uppercase
            {segment_id: "Coach"},  # title case
            {segment_id: "cOaCh"},  # mixed case
            {segment_id: "client"},  # lowercase
            {segment_id: "CLIENT"},  # uppercase
            {segment_id: "Client"},  # title case
            {segment_id: "cLiEnT"},  # mixed case
        ]

        for segment_roles in valid_cases:
            # Act - should not raise an exception
            result = self.use_case.execute(self.session_id, self.user_id, segment_roles)

            # Assert
            assert result["message"] == "Segment roles updated successfully"
            assert result["session_id"] == str(self.session_id)

    def test_execute_invalid_role(self):
        """Test error handling for invalid roles."""
        # Arrange
        segment_id = str(uuid4())
        self.session_repo.get_by_id.return_value = self.session

        # Test cases for invalid roles
        invalid_cases = [
            {segment_id: "teacher"},  # Wrong role
            {segment_id: ""},  # Empty role
            {segment_id: "invalid"},  # Invalid role
        ]

        for invalid_segment_roles in invalid_cases:
            with pytest.raises(
                ValueError,
                match="Invalid role.*Must be 'coach' or 'client'.*case-insensitive",
            ):
                self.use_case.execute(
                    self.session_id, self.user_id, invalid_segment_roles
                )


class TestSpeakerRoleRetrievalUseCase:
    """Test cases for SpeakerRoleRetrievalUseCase."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session_repo = Mock()
        self.speaker_role_repo = Mock()
        self.segment_role_repo = Mock()
        self.use_case = SpeakerRoleRetrievalUseCase(
            session_repo=self.session_repo,
            speaker_role_repo=self.speaker_role_repo,
            segment_role_repo=self.segment_role_repo,
        )

        # Common test data
        self.user_id = uuid4()
        self.session_id = uuid4()
        self.session = Session(
            id=self.session_id,
            user_id=self.user_id,
            status=SessionStatus.COMPLETED,
            audio_filename="test.wav",
            duration_seconds=60,
            title="Test Session",
            created_at=datetime.now(UTC),
        )

    def test_get_session_speaker_roles_success(self):
        """Test successful retrieval of speaker roles."""
        # Arrange
        mock_session_roles = [
            SessionRole(
                id=uuid4(),
                session_id=self.session_id,
                speaker_id=1,
                role=SpeakerRole.COACH,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
            SessionRole(
                id=uuid4(),
                session_id=self.session_id,
                speaker_id=2,
                role=SpeakerRole.CLIENT,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
        ]

        self.session_repo.get_by_id.return_value = self.session
        self.speaker_role_repo.get_by_session_id.return_value = mock_session_roles

        # Act
        result = self.use_case.get_session_speaker_roles(self.session_id, self.user_id)

        # Assert
        expected = {1: "COACH", 2: "CLIENT"}
        assert result == expected
        self.session_repo.get_by_id.assert_called_once_with(self.session_id)
        self.speaker_role_repo.get_by_session_id.assert_called_once_with(
            self.session_id
        )

    def test_get_segment_roles_success(self):
        """Test successful retrieval of segment roles."""
        # Arrange
        segment_id_1 = uuid4()
        segment_id_2 = uuid4()
        mock_segment_roles = [
            SegmentRole(
                id=uuid4(),
                session_id=self.session_id,
                segment_id=segment_id_1,
                role=SpeakerRole.COACH,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
            SegmentRole(
                id=uuid4(),
                session_id=self.session_id,
                segment_id=segment_id_2,
                role=SpeakerRole.CLIENT,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
        ]

        self.session_repo.get_by_id.return_value = self.session
        self.segment_role_repo.get_by_session_id.return_value = mock_segment_roles

        # Act
        result = self.use_case.get_segment_roles(self.session_id, self.user_id)

        # Assert
        expected = {str(segment_id_1): "COACH", str(segment_id_2): "CLIENT"}
        assert result == expected
        self.session_repo.get_by_id.assert_called_once_with(self.session_id)
        self.segment_role_repo.get_by_session_id.assert_called_once_with(
            self.session_id
        )


# Domain model validation tests
class TestSessionRoleDomainModel:
    """Test SessionRole domain model validation."""

    def test_session_role_creation_and_validation(self):
        """Test SessionRole domain model creation and validation."""
        # Valid creation
        role = SessionRole(
            session_id=uuid4(),
            speaker_id=1,
            role=SpeakerRole.COACH,
        )

        # Should not raise on validation
        role.validate()

        # Test business logic methods
        assert role.is_coach_role() is True
        assert role.is_client_role() is False

    def test_session_role_validation_errors(self):
        """Test SessionRole domain model validation errors."""
        # Invalid speaker_id
        with pytest.raises(ValueError, match="speaker_id must be positive"):
            role = SessionRole(
                session_id=uuid4(),
                speaker_id=0,
                role=SpeakerRole.COACH,
            )
            role.validate()

        # Missing session_id
        with pytest.raises(ValueError, match="session_id cannot be None"):
            role = SessionRole(
                session_id=None,
                speaker_id=1,
                role=SpeakerRole.COACH,
            )
            role.validate()


class TestSegmentRoleDomainModel:
    """Test SegmentRole domain model validation."""

    def test_segment_role_creation_and_validation(self):
        """Test SegmentRole domain model creation and validation."""
        # Valid creation
        role = SegmentRole(
            session_id=uuid4(),
            segment_id=uuid4(),
            role=SpeakerRole.CLIENT,
        )

        # Should not raise on validation
        role.validate()

        # Test business logic methods
        assert role.is_client_speaking() is True
        assert role.is_coach_speaking() is False

    def test_segment_role_validation_errors(self):
        """Test SegmentRole domain model validation errors."""
        # Missing session_id
        with pytest.raises(ValueError, match="session_id cannot be None"):
            role = SegmentRole(
                session_id=None,
                segment_id=uuid4(),
                role=SpeakerRole.CLIENT,
            )
            role.validate()

        # Missing segment_id
        with pytest.raises(ValueError, match="segment_id cannot be None"):
            role = SegmentRole(
                session_id=uuid4(),
                segment_id=None,
                role=SpeakerRole.CLIENT,
            )
            role.validate()


if __name__ == "__main__":
    # Run the tests manually for quick verification
    import sys

    print("🔴 TDD Red Phase: Running failing tests...")

    # Basic use case tests should pass but won't actually save data
    test_speaker_assignment = TestSpeakerRoleAssignmentUseCase()
    test_speaker_assignment.setup_method()

    try:
        test_speaker_assignment.test_execute_successful_assignment()
        print("✅ Basic use case test passed (but TODO means no saving)")
    except Exception as e:
        print(f"❌ Unexpected test failure: {e}")
        sys.exit(1)

    # Domain model tests should pass
    test_domain = TestSessionRoleDomainModel()
    test_domain.test_session_role_creation_and_validation()
    print("✅ Domain model tests passed")

    print(
        "🔴 TDD Red Phase: Current implementation incomplete - ready for Green phase!"
    )
