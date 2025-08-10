"""Tests for transcription Celery tasks."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from datetime import datetime

from coaching_assistant.tasks.transcription_tasks import transcribe_audio, _save_transcript_segments
from coaching_assistant.models.session import Session, SessionStatus
from coaching_assistant.models.transcript import TranscriptSegment
from coaching_assistant.services.stt_provider import TranscriptionResult, TranscriptSegment as STTSegment


@pytest.fixture
def mock_session():
    """Create a mock session."""
    session = Mock(spec=Session)
    session.id = uuid4()
    session.status = SessionStatus.PENDING
    session.gcs_audio_path = "gs://test-bucket/test.mp3"
    session.language = "zh-TW"
    session.update_status = Mock()
    session.mark_completed = Mock()
    session.mark_failed = Mock()
    return session


@pytest.fixture
def mock_transcription_result():
    """Create a mock transcription result."""
    segments = [
        STTSegment(
            speaker_id=1,
            start_sec=0.0,
            end_sec=5.0,
            content="你好世界",
            confidence=0.95
        ),
        STTSegment(
            speaker_id=2,
            start_sec=5.0,
            end_sec=10.0,
            content="Hello world",
            confidence=0.92
        )
    ]
    
    return TranscriptionResult(
        segments=segments,
        total_duration_sec=10.0,
        language_code="zh-TW",
        cost_usd=0.048,
        provider_metadata={"provider": "google_stt_v2"}
    )


class TestTranscribeAudioTask:
    """Test the transcribe_audio Celery task."""
    
    @patch('coaching_assistant.tasks.transcription_tasks.get_db_session')
    @patch('coaching_assistant.tasks.transcription_tasks.STTProviderFactory')
    @patch('coaching_assistant.tasks.transcription_tasks._save_transcript_segments')
    def test_transcribe_audio_success(
        self, 
        mock_save_segments, 
        mock_stt_factory, 
        mock_get_db_session,
        mock_session,
        mock_transcription_result
    ):
        """Test successful transcription."""
        # Setup mocks
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        mock_get_db_session.return_value.__enter__.return_value = mock_db
        mock_get_db_session.return_value.__exit__.return_value = None
        
        mock_provider = Mock()
        mock_provider.transcribe.return_value = mock_transcription_result
        mock_stt_factory.create.return_value = mock_provider
        
        # Create task with proper context
        task = transcribe_audio
        task.request = Mock()
        task.request.id = "test-task-id"
        task.request.retries = 0
        task.max_retries = 3
        
        # Execute task
        result = task(
            str(mock_session.id),
            "gs://test-bucket/test.mp3",
            "zh-TW"
        )
        
        # Verify calls
        mock_session.update_status.assert_any_call(SessionStatus.PROCESSING)
        mock_provider.transcribe.assert_called_once_with(
            audio_uri="gs://test-bucket/test.mp3",
            language="zh-TW",
            enable_diarization=True
        )
        mock_save_segments.assert_called_once()
        mock_session.mark_completed.assert_called_once()
        
        # Verify result
        assert result["status"] == "completed"
        assert result["segments_count"] == 2
        assert result["duration_sec"] == 10.0
        assert result["cost_usd"] == 0.048
    
    @patch('coaching_assistant.tasks.transcription_tasks.get_db_session')
    def test_transcribe_audio_session_not_found(self, mock_get_db_session):
        """Test task when session is not found."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db_session.return_value.__enter__.return_value = mock_db
        mock_get_db_session.return_value.__exit__.return_value = None
        
        task = transcribe_audio
        task.request = Mock()
        
        with pytest.raises(ValueError, match="Session .* not found"):
            task("nonexistent-session-id", "gs://test-bucket/test.mp3")
    
    @patch('coaching_assistant.tasks.transcription_tasks.get_db_session')
    @patch('coaching_assistant.tasks.transcription_tasks.STTProviderFactory')
    def test_transcribe_audio_stt_error(
        self, 
        mock_stt_factory, 
        mock_get_db_session,
        mock_session
    ):
        """Test transcription with STT provider error."""
        from coaching_assistant.services.stt_provider import STTProviderError
        
        # Setup mocks
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        mock_get_db_session.return_value.__enter__.return_value = mock_db
        mock_get_db_session.return_value.__exit__.return_value = None
        
        mock_provider = Mock()
        mock_provider.transcribe.side_effect = STTProviderError("API Error")
        mock_stt_factory.create.return_value = mock_provider
        
        task = transcribe_audio
        task.request = Mock()
        task.request.retries = 0
        task.max_retries = 3
        
        with pytest.raises(STTProviderError):
            task(str(mock_session.id), "gs://test-bucket/test.mp3")
        
        # Session should be marked as failed
        mock_session.mark_failed.assert_called_once()


class TestSaveTranscriptSegments:
    """Test the _save_transcript_segments function."""
    
    def test_save_transcript_segments(self):
        """Test saving transcript segments to database."""
        mock_db = Mock()
        session_id = uuid4()
        
        segments = [
            STTSegment(
                speaker_id=1,
                start_sec=0.0,
                end_sec=5.0,
                content="Hello",
                confidence=0.95
            ),
            STTSegment(
                speaker_id=2,
                start_sec=5.0,
                end_sec=10.0,
                content="World",
                confidence=0.92
            )
        ]
        
        _save_transcript_segments(mock_db, session_id, segments)
        
        # Verify db.add_all was called with correct number of segments
        mock_db.add_all.assert_called_once()
        called_segments = mock_db.add_all.call_args[0][0]
        assert len(called_segments) == 2
        
        # Verify segment data
        for i, db_segment in enumerate(called_segments):
            assert db_segment.session_id == session_id
            assert db_segment.speaker_id == segments[i].speaker_id
            assert db_segment.start_sec == segments[i].start_sec
            assert db_segment.end_sec == segments[i].end_sec
            assert db_segment.content == segments[i].content
            assert db_segment.confidence == segments[i].confidence
        
        mock_db.flush.assert_called_once()