"""Error handling tests for transcript upload use cases.

This test suite focuses on error paths, edge cases, and validation scenarios
for transcript parsing and upload functionality.
"""

from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

from coaching_assistant.core.models.coaching_session import CoachingSession
from coaching_assistant.core.models.session import (
    Session as TranscriptionSession,
)
from coaching_assistant.core.models.session import (
    SessionStatus,
)
from coaching_assistant.core.services.transcript_upload_use_case import (
    TranscriptParsingService,
    TranscriptUploadResult,
    TranscriptUploadUseCase,
)


class TestTranscriptParsingServiceErrorHandling:
    """Test error handling in TranscriptParsingService."""

    @pytest.fixture
    def parser(self):
        return TranscriptParsingService()

    def test_parse_vtt_with_empty_content(self, parser):
        """Test VTT parsing with empty content returns empty list."""
        result = parser.parse_vtt_content("")
        assert result == []

    def test_parse_vtt_with_only_header(self, parser):
        """Test VTT parsing with only WEBVTT header."""
        result = parser.parse_vtt_content("WEBVTT")
        assert result == []

    def test_parse_vtt_with_invalid_timestamps(self, parser):
        """Test VTT parsing handles invalid timestamp formats gracefully."""
        content = """WEBVTT

invalid timestamp
Speaker 1: Test content
"""
        result = parser.parse_vtt_content(content)
        assert result == []

    def test_parse_vtt_with_malformed_content(self, parser):
        """Test VTT parsing with malformed content structure."""
        content = """WEBVTT

00:00:01.000 -->
Speaker 1: Missing end timestamp
"""
        result = parser.parse_vtt_content(content)
        assert result == []

    def test_parse_vtt_with_missing_speaker_info(self, parser):
        """Test VTT parsing when speaker information is missing."""
        content = """WEBVTT

00:00:01.000 --> 00:00:02.000
Content without speaker prefix
"""
        result = parser.parse_vtt_content(content)
        assert len(result) == 1
        # Should default to speaker_id 1 when no speaker prefix found
        assert result[0].speaker_id == 1

    def test_parse_srt_with_empty_content(self, parser):
        """Test SRT parsing with empty content returns empty list."""
        result = parser.parse_srt_content("")
        assert result == []

    def test_parse_srt_with_invalid_block_structure(self, parser):
        """Test SRT parsing with invalid block structure."""
        content = """1
Invalid structure
"""
        result = parser.parse_srt_content(content)
        assert result == []

    def test_parse_srt_with_missing_timestamps(self, parser):
        """Test SRT parsing when timestamp line is missing."""
        content = """1
Speaker 1: Content without timestamp
"""
        result = parser.parse_srt_content(content)
        assert result == []

    def test_parse_srt_with_invalid_timestamp_format(self, parser):
        """Test SRT parsing with invalid timestamp format."""
        content = """1
invalid --> timestamp
Speaker 1: Test content
"""
        result = parser.parse_srt_content(content)
        assert result == []

    def test_parse_vtt_with_zero_duration_segment(self, parser):
        """Test VTT parsing handles segments with zero duration."""
        content = """WEBVTT

00:00:01.000 --> 00:00:01.000
Speaker 1: Zero duration segment
"""
        result = parser.parse_vtt_content(content)
        # Should still parse but duration will be 0
        assert len(result) == 1
        assert result[0].start_seconds == result[0].end_seconds

    def test_parse_vtt_with_negative_duration(self, parser):
        """Test VTT parsing when end time is before start time."""
        content = """WEBVTT

00:00:02.000 --> 00:00:01.000
Speaker 1: Negative duration
"""
        result = parser.parse_vtt_content(content)
        # Should parse but validation may catch this later
        if len(result) > 0:
            assert result[0].start_seconds > result[0].end_seconds


class TestTranscriptUploadUseCaseErrorHandling:
    """Test error handling in TranscriptUploadUseCase."""

    @pytest.fixture
    def mock_repos(self):
        return {
            "coaching_session_repo": Mock(),
            "session_repo": Mock(),
            "transcript_repo": Mock(),
            "speaker_role_repo": Mock(),
        }

    @pytest.fixture
    def use_case(self, mock_repos):
        return TranscriptUploadUseCase(
            coaching_session_repo=mock_repos["coaching_session_repo"],
            session_repo=mock_repos["session_repo"],
            transcript_repo=mock_repos["transcript_repo"],
            speaker_role_repo=mock_repos["speaker_role_repo"],
        )

    @pytest.fixture
    def mock_coaching_session(self):
        from datetime import date

        return CoachingSession(
            id=uuid4(),
            user_id=uuid4(),
            client_id=uuid4(),
            session_date=date(2024, 1, 1),
            duration_min=60,
            fee_amount=1000,
        )

    def test_upload_raises_error_when_coaching_session_not_found(
        self, use_case, mock_repos
    ):
        """Test upload fails when coaching session doesn't exist."""
        session_id = uuid4()
        user_id = uuid4()
        mock_repos["coaching_session_repo"].get_with_ownership_check.return_value = None

        with pytest.raises(ValueError) as exc_info:
            use_case.upload_transcript(
                coaching_session_id=session_id,
                user_id=user_id,
                file_content="WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nTest",
                file_name="test.vtt",
            )

        assert "not found or not accessible" in str(exc_info.value)

    def test_upload_raises_error_for_unsupported_file_format(
        self, use_case, mock_repos, mock_coaching_session
    ):
        """Test upload fails with unsupported file format."""
        mock_repos[
            "coaching_session_repo"
        ].get_with_ownership_check.return_value = mock_coaching_session

        with pytest.raises(ValueError) as exc_info:
            use_case.upload_transcript(
                coaching_session_id=mock_coaching_session.id,
                user_id=mock_coaching_session.user_id,
                file_content="Some content",
                file_name="test.txt",  # Unsupported format
            )

        assert "Unsupported file format" in str(exc_info.value)
        assert "txt" in str(exc_info.value)

    def test_upload_raises_error_when_no_valid_segments(
        self, use_case, mock_repos, mock_coaching_session
    ):
        """Test upload fails when file contains no valid segments."""
        mock_repos[
            "coaching_session_repo"
        ].get_with_ownership_check.return_value = mock_coaching_session

        with pytest.raises(ValueError) as exc_info:
            use_case.upload_transcript(
                coaching_session_id=mock_coaching_session.id,
                user_id=mock_coaching_session.user_id,
                file_content="WEBVTT\n\nInvalid content",  # No valid segments
                file_name="test.vtt",
            )

        assert "No valid segments found" in str(exc_info.value)

    def test_upload_raises_error_with_empty_file_content(
        self, use_case, mock_repos, mock_coaching_session
    ):
        """Test upload fails with empty file content."""
        mock_repos[
            "coaching_session_repo"
        ].get_with_ownership_check.return_value = mock_coaching_session

        with pytest.raises(ValueError) as exc_info:
            use_case.upload_transcript(
                coaching_session_id=mock_coaching_session.id,
                user_id=mock_coaching_session.user_id,
                file_content="",
                file_name="test.vtt",
            )

        assert "No valid segments found" in str(exc_info.value)

    def test_upload_handles_database_error_on_session_fetch(self, use_case, mock_repos):
        """Test upload handles database errors when fetching coaching session."""
        mock_repos[
            "coaching_session_repo"
        ].get_with_ownership_check.side_effect = OperationalError(
            "statement", "params", "orig"
        )

        with pytest.raises(OperationalError):
            use_case.upload_transcript(
                coaching_session_id=uuid4(),
                user_id=uuid4(),
                file_content="WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nTest",
                file_name="test.vtt",
            )

    def test_upload_handles_database_error_on_transcription_session_save(
        self, use_case, mock_repos, mock_coaching_session
    ):
        """Test upload handles database errors when saving transcription session."""
        mock_repos[
            "coaching_session_repo"
        ].get_with_ownership_check.return_value = mock_coaching_session
        mock_repos["session_repo"].save.side_effect = IntegrityError(
            "statement", "params", "orig"
        )

        with pytest.raises(IntegrityError):
            use_case.upload_transcript(
                coaching_session_id=mock_coaching_session.id,
                user_id=mock_coaching_session.user_id,
                file_content="WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nSpeaker 1: Test",
                file_name="test.vtt",
            )

    def test_upload_handles_database_error_on_transcript_save(
        self, use_case, mock_repos, mock_coaching_session
    ):
        """Test upload handles database errors when saving transcript segments."""
        mock_repos[
            "coaching_session_repo"
        ].get_with_ownership_check.return_value = mock_coaching_session

        # Session save succeeds
        mock_transcription_session = TranscriptionSession(
            id=uuid4(),
            user_id=mock_coaching_session.user_id,
            title="Test",
            language="en",
            status=SessionStatus.COMPLETED,
        )
        mock_repos["session_repo"].save.return_value = mock_transcription_session

        # Transcript save fails
        mock_repos["transcript_repo"].save_segments.side_effect = OperationalError(
            "statement", "params", "orig"
        )

        with pytest.raises(OperationalError):
            use_case.upload_transcript(
                coaching_session_id=mock_coaching_session.id,
                user_id=mock_coaching_session.user_id,
                file_content="WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nSpeaker 1: Test",
                file_name="test.vtt",
            )

    def test_upload_successfully_with_valid_vtt(
        self, use_case, mock_repos, mock_coaching_session
    ):
        """Test successful upload with valid VTT content."""
        mock_repos[
            "coaching_session_repo"
        ].get_with_ownership_check.return_value = mock_coaching_session

        mock_transcription_session = TranscriptionSession(
            id=uuid4(),
            user_id=mock_coaching_session.user_id,
            title="Test",
            language="en",
            status=SessionStatus.COMPLETED,
        )
        mock_repos["session_repo"].save.return_value = mock_transcription_session
        mock_repos["transcript_repo"].save_segments.return_value = None
        mock_repos["speaker_role_repo"].save.return_value = None

        result = use_case.upload_transcript(
            coaching_session_id=mock_coaching_session.id,
            user_id=mock_coaching_session.user_id,
            file_content="WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nSpeaker 1: Test",
            file_name="test.vtt",
        )

        assert isinstance(result, TranscriptUploadResult)
        assert result.segments_count == 1

    def test_upload_with_file_name_without_extension(
        self, use_case, mock_repos, mock_coaching_session
    ):
        """Test upload handles file name without extension."""
        mock_repos[
            "coaching_session_repo"
        ].get_with_ownership_check.return_value = mock_coaching_session

        with pytest.raises(ValueError) as exc_info:
            use_case.upload_transcript(
                coaching_session_id=mock_coaching_session.id,
                user_id=mock_coaching_session.user_id,
                file_content="WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nTest",
                file_name="test_no_extension",  # No file extension
            )

        assert "Unsupported file format" in str(exc_info.value)

    def test_upload_vtt_with_speaker_role_mapping(
        self, use_case, mock_repos, mock_coaching_session
    ):
        """Test upload applies speaker role mapping correctly."""
        mock_repos[
            "coaching_session_repo"
        ].get_with_ownership_check.return_value = mock_coaching_session

        mock_transcription_session = TranscriptionSession(
            id=uuid4(),
            user_id=mock_coaching_session.user_id,
            title="Test",
            language="en",
            status=SessionStatus.COMPLETED,
        )
        mock_repos["session_repo"].save.return_value = mock_transcription_session
        mock_repos["transcript_repo"].save_segments.return_value = None
        mock_repos["speaker_role_repo"].save.return_value = None

        result = use_case.upload_transcript(
            coaching_session_id=mock_coaching_session.id,
            user_id=mock_coaching_session.user_id,
            file_content="WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nSpeaker 1: Test content",
            file_name="test.vtt",
            speaker_role_mapping={"1": "coach"},
        )

        assert isinstance(result, TranscriptUploadResult)
        assert result.segments_count == 1

    def test_upload_srt_format_successfully(
        self, use_case, mock_repos, mock_coaching_session
    ):
        """Test upload handles SRT format correctly."""
        mock_repos[
            "coaching_session_repo"
        ].get_with_ownership_check.return_value = mock_coaching_session

        mock_transcription_session = TranscriptionSession(
            id=uuid4(),
            user_id=mock_coaching_session.user_id,
            title="Test",
            language="en",
            status=SessionStatus.COMPLETED,
        )
        mock_repos["session_repo"].save.return_value = mock_transcription_session
        mock_repos["transcript_repo"].save_segments.return_value = None
        mock_repos["speaker_role_repo"].save.return_value = None

        srt_content = """1
00:00:01,000 --> 00:00:02,000
Speaker 1: Test content
"""

        result = use_case.upload_transcript(
            coaching_session_id=mock_coaching_session.id,
            user_id=mock_coaching_session.user_id,
            file_content=srt_content,
            file_name="test.srt",
        )

        assert isinstance(result, TranscriptUploadResult)
        assert result.segments_count == 1

    def test_upload_with_very_long_transcript(
        self, use_case, mock_repos, mock_coaching_session
    ):
        """Test upload handles very long transcripts with many segments."""
        mock_repos[
            "coaching_session_repo"
        ].get_with_ownership_check.return_value = mock_coaching_session

        mock_transcription_session = TranscriptionSession(
            id=uuid4(),
            user_id=mock_coaching_session.user_id,
            title="Test",
            language="en",
            status=SessionStatus.COMPLETED,
        )
        mock_repos["session_repo"].save.return_value = mock_transcription_session
        mock_repos["transcript_repo"].save_segments.return_value = None
        mock_repos["speaker_role_repo"].save.return_value = None

        # Generate VTT with 100 segments
        segments = [
            f"00:00:{i:02d}.000 --> 00:00:{i + 1:02d}.000\nSpeaker 1: Segment {i}"
            for i in range(100)
        ]
        vtt_content = "WEBVTT\n\n" + "\n\n".join(segments)

        result = use_case.upload_transcript(
            coaching_session_id=mock_coaching_session.id,
            user_id=mock_coaching_session.user_id,
            file_content=vtt_content,
            file_name="long.vtt",
        )

        assert isinstance(result, TranscriptUploadResult)
        assert result.segments_count > 0
