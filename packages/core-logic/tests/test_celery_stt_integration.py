"""Integration tests for Celery + Google STT flow."""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from coaching_assistant.tasks.transcription_tasks import transcribe_audio
from coaching_assistant.services.google_stt import GoogleSTTProvider
from coaching_assistant.services.stt_provider import TranscriptionResult, TranscriptSegment
from coaching_assistant.core.database import get_db_session
from coaching_assistant.models.session import Session, SessionStatus


class TestCelerySTTIntegration:
    """Test Celery worker integration with Google STT service."""
    
    @patch('coaching_assistant.services.google_stt.speech_v2.SpeechClient')
    @patch('coaching_assistant.services.google_stt.settings')
    def test_google_stt_v2_configuration(self, mock_settings, mock_client):
        """Test Google STT v2 API configuration is correct."""
        # Setup mock settings
        mock_settings.GOOGLE_APPLICATION_CREDENTIALS_JSON = ""
        mock_settings.GOOGLE_PROJECT_ID = "test-project"
        mock_settings.MIN_SPEAKERS = 2
        mock_settings.MAX_SPEAKERS = 4
        
        # Test provider initialization
        provider = GoogleSTTProvider()
        
        # Test RecognitionFeatures creation without diarization
        with patch('coaching_assistant.services.google_stt.RecognitionFeatures') as mock_features, \
             patch('coaching_assistant.services.google_stt.RecognitionConfig') as mock_config:
            
            mock_features_instance = MagicMock()
            mock_features.return_value = mock_features_instance
            
            # Mock successful API call
            mock_operation = MagicMock()
            mock_operation.result.return_value.results = []
            mock_client.return_value.batch_recognize.return_value = mock_operation
            
            try:
                provider.transcribe("gs://test/audio.mp3", "zh-TW", enable_diarization=False)
            except:
                pass  # We're testing configuration, not the full flow
            
            # Verify features are configured correctly
            mock_features.assert_called_once_with(
                enable_automatic_punctuation=True,
                enable_word_time_offsets=True,
                enable_word_confidence=True
            )
    
    @patch('coaching_assistant.services.google_stt.speech_v2.SpeechClient')
    @patch('coaching_assistant.services.google_stt.settings')
    def test_speaker_diarization_v2_config(self, mock_settings, mock_client):
        """Test speaker diarization configuration for v2 API."""
        mock_settings.GOOGLE_APPLICATION_CREDENTIALS_JSON = ""
        mock_settings.GOOGLE_PROJECT_ID = "test-project"
        mock_settings.MIN_SPEAKERS = 2
        mock_settings.MAX_SPEAKERS = 4
        
        provider = GoogleSTTProvider()
        
        with patch('coaching_assistant.services.google_stt.RecognitionFeatures') as mock_features, \
             patch('coaching_assistant.services.google_stt.SpeakerDiarizationConfig') as mock_diarization:
            
            mock_features_instance = MagicMock()
            mock_features.return_value = mock_features_instance
            
            mock_diarization_instance = MagicMock()
            mock_diarization.return_value = mock_diarization_instance
            
            # Mock successful API call
            mock_operation = MagicMock()
            mock_operation.result.return_value.results = []
            mock_client.return_value.batch_recognize.return_value = mock_operation
            
            try:
                provider.transcribe("gs://test/audio.mp3", "zh-TW", enable_diarization=True)
            except:
                pass
            
            # Verify diarization config created correctly (no enable_speaker_diarization field)
            mock_diarization.assert_called_once_with(
                min_speaker_count=2,
                max_speaker_count=4
            )
            
            # Verify it was assigned to features
            assert mock_features_instance.diarization_config == mock_diarization_instance
    
    @patch('coaching_assistant.tasks.transcription_tasks.get_db_session')
    @patch('coaching_assistant.tasks.transcription_tasks.STTProviderFactory')
    def test_transcribe_audio_task_success(self, mock_stt_factory, mock_db_session):
        """Test successful transcription task execution."""
        # Setup mocks
        session_id = str(uuid4())
        gcs_uri = "gs://test-bucket/audio.mp3"
        language = "zh-TW"
        
        # Mock database session
        mock_db = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_db
        
        mock_session = MagicMock()
        mock_session.id = session_id
        mock_session.status = SessionStatus.PENDING
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        
        # Mock STT provider
        mock_provider = MagicMock()
        mock_stt_factory.create.return_value = mock_provider
        
        # Mock transcription result
        mock_segments = [
            TranscriptSegment(
                speaker_id=1,
                start_sec=0.0,
                end_sec=2.5,
                content="Test transcription content",
                confidence=0.95
            )
        ]
        
        mock_result = TranscriptionResult(
            segments=mock_segments,
            total_duration_sec=2.5,
            language_code="zh-TW",
            cost_usd=0.012,
            provider_metadata={"provider": "google_stt_v2"}
        )
        
        mock_provider.transcribe.return_value = mock_result
        
        # Execute task
        result = transcribe_audio(session_id, gcs_uri, language)
        
        # Verify result
        assert result is not None
        assert "session_id" in result
        assert result["session_id"] == session_id
        
        # Verify STT provider was called correctly
        mock_provider.transcribe.assert_called_once_with(
            audio_uri=gcs_uri,
            language=language,
            enable_diarization=True  # Default value
        )
        
        # Verify session was updated
        assert mock_session.status == SessionStatus.PROCESSING
    
    @patch('coaching_assistant.tasks.transcription_tasks.get_db_session')
    @patch('coaching_assistant.tasks.transcription_tasks.STTProviderFactory')
    def test_transcribe_audio_task_stt_error(self, mock_stt_factory, mock_db_session):
        """Test transcription task with STT provider error."""
        from coaching_assistant.services.stt_provider import STTProviderError
        
        session_id = str(uuid4())
        gcs_uri = "gs://test-bucket/audio.mp3"
        language = "zh-TW"
        
        # Mock database session
        mock_db = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_db
        
        mock_session = MagicMock()
        mock_session.id = session_id
        mock_db.query.return_value.filter.return_value.first.return_value = mock_session
        
        # Mock STT provider with error
        mock_provider = MagicMock()
        mock_provider.transcribe.side_effect = STTProviderError("Recognition features configuration error")
        mock_stt_factory.create.return_value = mock_provider
        
        # Execute task and expect error
        with pytest.raises(STTProviderError):
            transcribe_audio(session_id, gcs_uri, language)
        
        # Verify session was marked as failed
        mock_session.mark_failed.assert_called_once()
    
    @patch('coaching_assistant.services.google_stt.speech_v2.SpeechClient')
    @patch('coaching_assistant.services.google_stt.settings')
    def test_credentials_decoding_integration(self, mock_settings, mock_client):
        """Test Base64 credentials decoding in real scenario."""
        import base64
        import json
        
        # Setup Base64 encoded credentials
        test_credentials = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "key123",
            "private_key": "-----BEGIN PRIVATE KEY-----\\ntest\\n-----END PRIVATE KEY-----",
            "client_email": "test@test.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
        
        encoded_creds = base64.b64encode(json.dumps(test_credentials).encode()).decode()
        
        mock_settings.GOOGLE_APPLICATION_CREDENTIALS_JSON = encoded_creds
        mock_settings.GOOGLE_PROJECT_ID = "test-project"
        
        with patch('coaching_assistant.services.google_stt.service_account') as mock_service_account:
            mock_credentials = MagicMock()
            mock_service_account.Credentials.from_service_account_info.return_value = mock_credentials
            
            # This should not raise an error
            provider = GoogleSTTProvider()
            assert provider.project_id == "test-project"
            
            # Verify credentials were decoded and used
            mock_service_account.Credentials.from_service_account_info.assert_called_once_with(test_credentials)
    
    def test_segment_processing_v2_format(self):
        """Test processing segments with v2 API word format."""
        with patch('coaching_assistant.services.google_stt.speech_v2.SpeechClient'), \
             patch('coaching_assistant.services.google_stt.settings') as mock_settings:
            
            mock_settings.GOOGLE_APPLICATION_CREDENTIALS_JSON = ""
            mock_settings.GOOGLE_PROJECT_ID = "test-project"
            
            provider = GoogleSTTProvider()
            
            # Create mock words in v2 API format
            mock_words = []
            test_words = [
                ("你好", 0.0, 0.8, 0.95, "1"),
                ("我是", 0.8, 1.2, 0.92, "1"),
                ("教練", 1.2, 1.8, 0.90, "1"),
                ("很高興", 2.0, 2.6, 0.93, "2"),
                ("見到你", 2.6, 3.2, 0.91, "2")
            ]
            
            for word, start, end, conf, speaker in test_words:
                mock_word = MagicMock()
                mock_word.word = word
                mock_word.start_offset.total_seconds.return_value = start
                mock_word.end_offset.total_seconds.return_value = end
                mock_word.confidence = conf
                mock_word.speaker_label = speaker
                mock_words.append(mock_word)
            
            # Group words by speaker
            speaker_1_words = [w for w in mock_words if w.speaker_label == "1"]
            speaker_2_words = [w for w in mock_words if w.speaker_label == "2"]
            
            # Test segment creation for each speaker
            segment_1 = provider._create_segment_from_words(speaker_1_words, speaker_id=1)
            segment_2 = provider._create_segment_from_words(speaker_2_words, speaker_id=2)
            
            # Verify Speaker 1 segment
            assert segment_1.speaker_id == 1
            assert segment_1.content == "你好 我是 教練"
            assert segment_1.start_sec == 0.0
            assert segment_1.end_sec == 1.8
            assert segment_1.confidence == pytest.approx(0.92, abs=0.01)  # Average confidence
            
            # Verify Speaker 2 segment
            assert segment_2.speaker_id == 2
            assert segment_2.content == "很高興 見到你"
            assert segment_2.start_sec == 2.0
            assert segment_2.end_sec == 3.2
            assert segment_2.confidence == pytest.approx(0.92, abs=0.01)  # Average confidence
    
    def test_language_detection_integration(self):
        """Test language detection and configuration."""
        with patch('coaching_assistant.services.google_stt.speech_v2.SpeechClient'), \
             patch('coaching_assistant.services.google_stt.settings') as mock_settings:
            
            mock_settings.GOOGLE_APPLICATION_CREDENTIALS_JSON = ""
            mock_settings.GOOGLE_PROJECT_ID = "test-project"
            
            provider = GoogleSTTProvider()
            
            # Test specific language
            with patch('coaching_assistant.services.google_stt.RecognitionConfig') as mock_config:
                mock_operation = MagicMock()
                mock_operation.result.return_value.results = []
                
                with patch.object(provider, 'client') as mock_client:
                    mock_client.batch_recognize.return_value = mock_operation
                    
                    try:
                        provider.transcribe("gs://test/audio.mp3", "zh-TW")
                    except:
                        pass
                    
                    # Verify language was set correctly
                    args, kwargs = mock_config.call_args
                    assert "language_codes" in kwargs
                    assert kwargs["language_codes"] == ["zh-TW"]
            
            # Test auto-detection
            with patch('coaching_assistant.services.google_stt.RecognitionConfig') as mock_config:
                mock_operation = MagicMock()
                mock_operation.result.return_value.results = []
                
                with patch.object(provider, 'client') as mock_client:
                    mock_client.batch_recognize.return_value = mock_operation
                    
                    try:
                        provider.transcribe("gs://test/audio.mp3", "auto")
                    except:
                        pass
                    
                    # Verify auto-detection languages
                    args, kwargs = mock_config.call_args
                    assert "language_codes" in kwargs
                    expected_langs = ["zh-TW", "zh-CN", "en-US"]
                    assert kwargs["language_codes"] == expected_langs


if __name__ == "__main__":
    # Run pytest on this file
    pytest.main([__file__, "-v"])