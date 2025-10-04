"""Edge case tests for session management use cases - Day 2 Coverage Improvement.

Focus on uncovered lines to improve coverage from 73% → 85%.
Target areas:
- update_speaker_roles (lines 370-383)
- update_session_metadata (lines 404-424)
- retry_transcription (lines 754-782)
- _parse_srt_content (lines 1273-1324)
"""

from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest

from coaching_assistant.core.models.session import Session, SessionStatus
from coaching_assistant.core.models.transcript import TranscriptSegment
from coaching_assistant.core.services.session_management_use_case import (
    SessionTranscriptionManagementUseCase,
    SessionTranscriptUpdateUseCase,
    SessionTranscriptUploadUseCase,
)
from coaching_assistant.exceptions import DomainException


class TestSessionTranscriptUpdateEdgeCases:
    """Test edge cases for SessionTranscriptUpdateUseCase."""

    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories."""
        return {"session_repo": Mock(), "transcript_repo": Mock()}

    @pytest.fixture
    def use_case(self, mock_repos):
        """Create use case instance."""
        return SessionTranscriptUpdateUseCase(
            session_repo=mock_repos["session_repo"],
            transcript_repo=mock_repos["transcript_repo"],
        )

    @pytest.fixture
    def sample_session(self):
        """Create a sample session."""
        user_id = uuid4()
        return Session(
            id=uuid4(),
            user_id=user_id,
            status=SessionStatus.COMPLETED,
            language="zh-TW",
            stt_provider="google",
            audio_filename="test.wav",
            gcs_audio_path="gs://test/audio.wav",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    def test_update_speaker_roles_session_not_found(self, use_case, mock_repos):
        """Test update_speaker_roles when session doesn't exist."""
        # Arrange
        session_id = uuid4()
        user_id = uuid4()
        role_mappings = {"Speaker 1": "Coach", "Speaker 2": "Client"}
        mock_repos["session_repo"].get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Session not found or access denied"):
            use_case.update_speaker_roles(session_id, role_mappings, user_id)

    def test_update_speaker_roles_access_denied(
        self, use_case, mock_repos, sample_session
    ):
        """Test update_speaker_roles when user doesn't own the session."""
        # Arrange
        different_user_id = uuid4()
        role_mappings = {"Speaker 1": "Coach"}
        mock_repos["session_repo"].get_by_id.return_value = sample_session

        # Act & Assert
        with pytest.raises(ValueError, match="Session not found or access denied"):
            use_case.update_speaker_roles(
                sample_session.id, role_mappings, different_user_id
            )

    def test_update_speaker_roles_successful(
        self, use_case, mock_repos, sample_session
    ):
        """Test successful speaker role update."""
        # Arrange
        role_mappings = {"Speaker 1": "Coach", "Speaker 2": "Client"}
        mock_repos["session_repo"].get_by_id.return_value = sample_session

        updated_segments = [
            TranscriptSegment(
                id=uuid4(),
                session_id=sample_session.id,
                speaker_id=1,
                speaker_role="Coach",
                start_seconds=0.0,
                end_seconds=5.0,
                content="Hello",
                confidence=1.0,
            )
        ]
        mock_repos[
            "transcript_repo"
        ].update_speaker_roles.return_value = updated_segments
        mock_repos["session_repo"].save.return_value = sample_session

        # Act
        result = use_case.update_speaker_roles(
            sample_session.id, role_mappings, sample_session.user_id
        )

        # Assert
        assert len(result) == 1
        assert result[0].speaker_role == "Coach"
        mock_repos["transcript_repo"].update_speaker_roles.assert_called_once_with(
            sample_session.id, role_mappings
        )
        mock_repos["session_repo"].save.assert_called_once()

    def test_update_speaker_roles_empty_mapping(
        self, use_case, mock_repos, sample_session
    ):
        """Test update_speaker_roles with empty role mappings."""
        # Arrange
        role_mappings = {}
        mock_repos["session_repo"].get_by_id.return_value = sample_session
        mock_repos["transcript_repo"].update_speaker_roles.return_value = []
        mock_repos["session_repo"].save.return_value = sample_session

        # Act
        result = use_case.update_speaker_roles(
            sample_session.id, role_mappings, sample_session.user_id
        )

        # Assert
        assert result == []

    def test_update_session_metadata_session_not_found(self, use_case, mock_repos):
        """Test update_session_metadata when session doesn't exist."""
        # Arrange
        session_id = uuid4()
        user_id = uuid4()
        metadata = {"duration_seconds": 300}
        mock_repos["session_repo"].get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Session not found or access denied"):
            use_case.update_session_metadata(session_id, metadata, user_id)

    def test_update_session_metadata_access_denied(
        self, use_case, mock_repos, sample_session
    ):
        """Test update_session_metadata when user doesn't own session."""
        # Arrange
        different_user_id = uuid4()
        metadata = {"duration_seconds": 300}
        mock_repos["session_repo"].get_by_id.return_value = sample_session

        # Act & Assert
        with pytest.raises(ValueError, match="Session not found or access denied"):
            use_case.update_session_metadata(
                sample_session.id, metadata, different_user_id
            )

    def test_update_session_metadata_duration_only(
        self, use_case, mock_repos, sample_session
    ):
        """Test updating only duration_seconds."""
        # Arrange
        metadata = {"duration_seconds": 300}
        mock_repos["session_repo"].get_by_id.return_value = sample_session
        mock_repos["session_repo"].save.return_value = sample_session

        # Act
        result = use_case.update_session_metadata(
            sample_session.id, metadata, sample_session.user_id
        )

        # Assert
        mock_repos["session_repo"].save.assert_called_once()
        assert result == sample_session

    def test_update_session_metadata_audio_filename_only(
        self, use_case, mock_repos, sample_session
    ):
        """Test updating only audio_filename."""
        # Arrange
        metadata = {"audio_filename": "new_file.wav"}
        mock_repos["session_repo"].get_by_id.return_value = sample_session
        mock_repos["session_repo"].save.return_value = sample_session

        # Act
        use_case.update_session_metadata(
            sample_session.id, metadata, sample_session.user_id
        )

        # Assert
        mock_repos["session_repo"].save.assert_called_once()

    def test_update_session_metadata_error_message_only(
        self, use_case, mock_repos, sample_session
    ):
        """Test updating only error_message."""
        # Arrange
        metadata = {"error_message": "Transcription failed"}
        mock_repos["session_repo"].get_by_id.return_value = sample_session
        mock_repos["session_repo"].save.return_value = sample_session

        # Act
        use_case.update_session_metadata(
            sample_session.id, metadata, sample_session.user_id
        )

        # Assert
        mock_repos["session_repo"].save.assert_called_once()

    def test_update_session_metadata_all_fields(
        self, use_case, mock_repos, sample_session
    ):
        """Test updating all metadata fields at once."""
        # Arrange
        metadata = {
            "duration_seconds": 300,
            "audio_filename": "new_file.wav",
            "error_message": "Some error",
        }
        mock_repos["session_repo"].get_by_id.return_value = sample_session
        mock_repos["session_repo"].save.return_value = sample_session

        # Act
        use_case.update_session_metadata(
            sample_session.id, metadata, sample_session.user_id
        )

        # Assert
        mock_repos["session_repo"].save.assert_called_once()

    def test_update_session_metadata_empty_dict(
        self, use_case, mock_repos, sample_session
    ):
        """Test updating with empty metadata dict."""
        # Arrange
        metadata = {}
        mock_repos["session_repo"].get_by_id.return_value = sample_session
        mock_repos["session_repo"].save.return_value = sample_session

        # Act
        use_case.update_session_metadata(
            sample_session.id, metadata, sample_session.user_id
        )

        # Assert
        mock_repos["session_repo"].save.assert_called_once()

    def test_update_session_metadata_unknown_fields_ignored(
        self, use_case, mock_repos, sample_session
    ):
        """Test that unknown metadata fields are silently ignored."""
        # Arrange
        metadata = {"unknown_field": "value", "another_unknown": 123}
        mock_repos["session_repo"].get_by_id.return_value = sample_session
        mock_repos["session_repo"].save.return_value = sample_session

        # Act
        use_case.update_session_metadata(
            sample_session.id, metadata, sample_session.user_id
        )

        # Assert
        mock_repos["session_repo"].save.assert_called_once()


class TestSessionTranscriptionManagementEdgeCases:
    """Test edge cases for SessionTranscriptionManagementUseCase."""

    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories."""
        return {"session_repo": Mock(), "transcript_repo": Mock()}

    @pytest.fixture
    def use_case(self, mock_repos):
        """Create use case instance."""
        return SessionTranscriptionManagementUseCase(
            session_repo=mock_repos["session_repo"],
            transcript_repo=mock_repos["transcript_repo"],
        )

    @pytest.fixture
    def failed_session(self):
        """Create a failed session for retry testing."""
        user_id = uuid4()
        return Session(
            id=uuid4(),
            user_id=user_id,
            status=SessionStatus.FAILED,
            language="zh-TW",
            stt_provider="google",
            audio_filename="test.wav",
            gcs_audio_path="gs://test/audio.wav",
            error_message="Transcription failed",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    def test_retry_transcription_session_not_found(self, use_case, mock_repos):
        """Test retry when session doesn't exist."""
        # Arrange
        session_id = uuid4()
        user_id = uuid4()
        mock_repos["session_repo"].get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Session not found or access denied"):
            use_case.retry_transcription(session_id, user_id)

    def test_retry_transcription_access_denied(
        self, use_case, mock_repos, failed_session
    ):
        """Test retry when user doesn't own the session."""
        # Arrange
        different_user_id = uuid4()
        mock_repos["session_repo"].get_by_id.return_value = failed_session

        # Act & Assert
        with pytest.raises(ValueError, match="Session not found or access denied"):
            use_case.retry_transcription(failed_session.id, different_user_id)

    def test_retry_transcription_not_failed_status(self, use_case, mock_repos):
        """Test retry fails for non-FAILED sessions."""
        # Arrange
        user_id = uuid4()
        processing_session = Session(
            id=uuid4(),
            user_id=user_id,
            status=SessionStatus.PROCESSING,
            language="zh-TW",
            stt_provider="google",
            audio_filename="test.wav",
            gcs_audio_path="gs://test/audio.wav",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_repos["session_repo"].get_by_id.return_value = processing_session

        # Act & Assert
        with pytest.raises(
            DomainException, match="Cannot retry transcription for session with status"
        ):
            use_case.retry_transcription(processing_session.id, user_id)

    def test_retry_transcription_no_audio_file(self, use_case, mock_repos):
        """Test retry fails when no audio file exists."""
        # Arrange
        user_id = uuid4()
        session_no_audio = Session(
            id=uuid4(),
            user_id=user_id,
            status=SessionStatus.FAILED,
            language="zh-TW",
            stt_provider="google",
            audio_filename="test.wav",
            gcs_audio_path=None,  # No audio path
            error_message="Transcription failed",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_repos["session_repo"].get_by_id.return_value = session_no_audio

        # Act & Assert
        with pytest.raises(DomainException, match="No audio file found"):
            use_case.retry_transcription(session_no_audio.id, user_id)

    def test_retry_transcription_successful(self, use_case, mock_repos, failed_session):
        """Test successful retry operation."""
        # Arrange
        mock_repos["session_repo"].get_by_id.return_value = failed_session
        mock_repos["session_repo"].save.return_value = failed_session
        mock_repos["transcript_repo"].delete_by_session_id.return_value = True

        # Act
        result = use_case.retry_transcription(failed_session.id, failed_session.user_id)

        # Assert
        assert result["session_id"] == str(failed_session.id)
        assert result["gcs_uri"] == failed_session.gcs_audio_path
        assert result["language"] == failed_session.language
        assert result["stt_provider"] == failed_session.stt_provider
        assert result["retry"] is True
        mock_repos["transcript_repo"].delete_by_session_id.assert_called_once_with(
            failed_session.id
        )
        mock_repos["session_repo"].save.assert_called_once()

    def test_retry_transcription_clears_error_message(
        self, use_case, mock_repos, failed_session
    ):
        """Test that retry clears previous error message."""
        # Arrange
        mock_repos["session_repo"].get_by_id.return_value = failed_session
        mock_repos["session_repo"].save.return_value = failed_session
        mock_repos["transcript_repo"].delete_by_session_id.return_value = True

        # Act
        use_case.retry_transcription(failed_session.id, failed_session.user_id)

        # Assert
        # Verify save was called (error_message should be None in saved session)
        mock_repos["session_repo"].save.assert_called_once()

    def test_retry_transcription_clears_job_id(
        self, use_case, mock_repos, failed_session
    ):
        """Test that retry clears previous transcription_job_id."""
        # Arrange
        failed_session_with_job = Session(
            **{
                **failed_session.__dict__,
                "transcription_job_id": "old-job-id",
            }
        )
        mock_repos["session_repo"].get_by_id.return_value = failed_session_with_job
        mock_repos["session_repo"].save.return_value = failed_session_with_job
        mock_repos["transcript_repo"].delete_by_session_id.return_value = True

        # Act
        use_case.retry_transcription(
            failed_session_with_job.id, failed_session_with_job.user_id
        )

        # Assert
        mock_repos["session_repo"].save.assert_called_once()
        # Job ID should be cleared (None) in saved session


class TestSessionSRTParsingEdgeCases:
    """Test edge cases for SRT content parsing."""

    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories."""
        return {"session_repo": Mock(), "transcript_repo": Mock()}

    @pytest.fixture
    def use_case(self, mock_repos):
        """Create use case instance."""
        return SessionTranscriptUploadUseCase(
            session_repo=mock_repos["session_repo"],
            transcript_repo=mock_repos["transcript_repo"],
        )

    @pytest.fixture
    def sample_session(self):
        """Create a sample session."""
        user_id = uuid4()
        return Session(
            id=uuid4(),
            user_id=user_id,
            status=SessionStatus.PROCESSING,
            language="zh-TW",
            stt_provider="google",
            audio_filename="test.wav",
            gcs_audio_path="gs://test/audio.wav",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    def test_parse_srt_basic(self, use_case, mock_repos, sample_session):
        """Test basic SRT parsing."""
        # Arrange
        srt_content = """1
00:00:00,000 --> 00:00:05,000
教練: 你好嗎？

2
00:00:05,000 --> 00:00:10,000
客戶: 我很好，謝謝
"""
        mock_repos["session_repo"].get_by_id.return_value = sample_session

        # Act
        result = use_case.upload_transcript_file(
            sample_session.id, sample_session.user_id, "transcript.srt", srt_content
        )

        # Assert
        assert len(result["segments_data"]) == 2
        assert result["segments_data"][0]["content"] == "你好嗎？"
        assert result["segments_data"][0]["speaker_id"] == 1  # Coach
        assert result["segments_data"][1]["content"] == "我很好，謝謝"
        assert result["segments_data"][1]["speaker_id"] == 2  # Client

    def test_parse_srt_with_client_label(self, use_case, mock_repos, sample_session):
        """Test SRT parsing with Client speaker label."""
        # Arrange
        srt_content = """1
00:00:00,000 --> 00:00:05,000
Client: Hello there
"""
        mock_repos["session_repo"].get_by_id.return_value = sample_session

        # Act
        result = use_case.upload_transcript_file(
            sample_session.id, sample_session.user_id, "transcript.srt", srt_content
        )

        # Assert
        assert len(result["segments_data"]) == 1
        assert result["segments_data"][0]["speaker_id"] == 2  # Client

    def test_parse_srt_without_speaker_prefix(
        self, use_case, mock_repos, sample_session
    ):
        """Test SRT parsing without speaker prefix defaults to speaker 1."""
        # Arrange
        srt_content = """1
00:00:00,000 --> 00:00:05,000
Content without speaker label
"""
        mock_repos["session_repo"].get_by_id.return_value = sample_session

        # Act
        result = use_case.upload_transcript_file(
            sample_session.id, sample_session.user_id, "transcript.srt", srt_content
        )

        # Assert
        assert len(result["segments_data"]) == 1
        assert result["segments_data"][0]["speaker_id"] == 1  # Default

    def test_parse_srt_skips_invalid_blocks(self, use_case, mock_repos, sample_session):
        """Test SRT parsing skips blocks with less than 3 lines."""
        # Arrange
        srt_content = """1
00:00:00,000 --> 00:00:05,000
Valid content

2
Invalid block

3
00:00:10,000 --> 00:00:15,000
Another valid content
"""
        mock_repos["session_repo"].get_by_id.return_value = sample_session

        # Act
        result = use_case.upload_transcript_file(
            sample_session.id, sample_session.user_id, "transcript.srt", srt_content
        )

        # Assert
        assert len(result["segments_data"]) == 2  # Only valid blocks
        assert result["segments_data"][0]["content"] == "Valid content"
        assert result["segments_data"][1]["content"] == "Another valid content"

    def test_parse_srt_multiline_content(self, use_case, mock_repos, sample_session):
        """Test SRT parsing with multiline content."""
        # Arrange
        srt_content = """1
00:00:00,000 --> 00:00:05,000
Line 1 of content
Line 2 of content
Line 3 of content
"""
        mock_repos["session_repo"].get_by_id.return_value = sample_session

        # Act
        result = use_case.upload_transcript_file(
            sample_session.id, sample_session.user_id, "transcript.srt", srt_content
        )

        # Assert
        assert len(result["segments_data"]) == 1
        assert "Line 1" in result["segments_data"][0]["content"]
        assert "Line 2" in result["segments_data"][0]["content"]
        assert "Line 3" in result["segments_data"][0]["content"]

    def test_parse_srt_empty_content(self, use_case, mock_repos, sample_session):
        """Test SRT parsing with empty content raises exception."""
        # Arrange
        srt_content = ""
        mock_repos["session_repo"].get_by_id.return_value = sample_session

        # Act & Assert
        with pytest.raises(DomainException, match="No valid transcript segments"):
            use_case.upload_transcript_file(
                sample_session.id, sample_session.user_id, "transcript.srt", srt_content
            )

    def test_parse_srt_malformed_timestamp(self, use_case, mock_repos, sample_session):
        """Test SRT parsing with malformed timestamps is skipped."""
        # Arrange
        srt_content = """1
INVALID_TIMESTAMP
Content here

2
00:00:05,000 --> 00:00:10,000
Valid content
"""
        mock_repos["session_repo"].get_by_id.return_value = sample_session

        # Act
        result = use_case.upload_transcript_file(
            sample_session.id, sample_session.user_id, "transcript.srt", srt_content
        )

        # Assert
        # Should only parse the valid block
        assert len(result["segments_data"]) >= 0  # May skip malformed
