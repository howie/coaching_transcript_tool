"""Tests for STT provider implementations."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from coaching_assistant.services.stt_provider import (
    TranscriptSegment, 
    TranscriptionResult,
    STTProviderError
)
from coaching_assistant.services.google_stt import GoogleSTTProvider
from coaching_assistant.services.stt_factory import STTProviderFactory


class TestTranscriptSegment:
    """Test TranscriptSegment dataclass."""
    
    def test_duration_calculation(self):
        segment = TranscriptSegment(
            speaker_id=1,
            start_sec=10.5,
            end_sec=15.3,
            content="Hello world",
            confidence=0.95
        )
        
        assert abs(segment.duration_sec - 4.8) < 0.001  # Handle floating point precision


class TestSTTProviderFactory:
    """Test STT provider factory."""
    
    def test_create_google_provider(self):
        """Test creating Google STT provider."""
        with patch('coaching_assistant.services.google_stt.GoogleSTTProvider.__init__', return_value=None):
            provider = STTProviderFactory.create("google")
            assert isinstance(provider, GoogleSTTProvider)
    
    def test_create_default_provider(self):
        """Test creating default provider (Google)."""
        with patch('coaching_assistant.services.google_stt.GoogleSTTProvider.__init__', return_value=None):
            provider = STTProviderFactory.create()
            assert isinstance(provider, GoogleSTTProvider)
    
    def test_create_unsupported_provider(self):
        """Test creating unsupported provider raises error."""
        with pytest.raises(ValueError, match="Unsupported STT provider type"):
            STTProviderFactory.create("unsupported")
    
    def test_whisper_not_implemented(self):
        """Test Whisper provider not yet implemented."""
        with pytest.raises(NotImplementedError, match="Whisper STT provider not yet implemented"):
            STTProviderFactory.create("whisper")
    
    def test_get_available_providers(self):
        """Test getting available providers."""
        providers = STTProviderFactory.get_available_providers()
        assert "google" in providers


class TestGoogleSTTProvider:
    """Test Google STT provider."""
    
    @patch('coaching_assistant.services.google_stt.speech_v2.SpeechClient')
    @patch('coaching_assistant.services.google_stt.settings')
    def test_initialization(self, mock_settings, mock_client):
        """Test Google STT provider initialization."""
        mock_settings.GOOGLE_APPLICATION_CREDENTIALS_JSON = ""
        mock_settings.GOOGLE_PROJECT_ID = "test-project"
        
        provider = GoogleSTTProvider()
        assert provider.provider_name == "google_stt_v2"
        mock_client.assert_called_once()
    
    @patch('coaching_assistant.services.google_stt.speech_v2.SpeechClient')
    @patch('coaching_assistant.services.google_stt.settings')
    def test_initialization_with_credentials(self, mock_settings, mock_client):
        """Test initialization with JSON credentials."""
        mock_settings.GOOGLE_APPLICATION_CREDENTIALS_JSON = '{"type": "service_account"}'
        mock_settings.GOOGLE_PROJECT_ID = "test-project"
        
        with patch('coaching_assistant.services.google_stt.service_account'):
            provider = GoogleSTTProvider()
            assert provider.project_id == "test-project"
    
    @patch('coaching_assistant.services.google_stt.speech_v2.SpeechClient')
    @patch('coaching_assistant.services.google_stt.settings')
    def test_estimate_cost(self, mock_settings, mock_client):
        """Test cost estimation."""
        mock_settings.GOOGLE_APPLICATION_CREDENTIALS_JSON = ""
        mock_settings.GOOGLE_PROJECT_ID = "test-project"
        
        provider = GoogleSTTProvider()
        
        # 60 seconds = 1 minute = $0.048
        cost = provider.estimate_cost(60)
        assert cost == Decimal("0.048")
        
        # 300 seconds = 5 minutes = $0.24
        cost = provider.estimate_cost(300)
        assert cost == Decimal("0.240")
    
    @patch('coaching_assistant.services.google_stt.speech_v2.SpeechClient')
    @patch('coaching_assistant.services.google_stt.settings')
    def test_transcribe_success(self, mock_settings, mock_client):
        """Test successful transcription with v2 API."""
        mock_settings.GOOGLE_APPLICATION_CREDENTIALS_JSON = ""
        mock_settings.GOOGLE_PROJECT_ID = "test-project"
        
        # Mock the recognition result for v2 API
        mock_word = MagicMock()
        mock_word.word = "Hello"
        mock_word.speaker_label = "1"  # v2 API uses speaker_label instead of speaker_tag
        mock_word.start_offset.total_seconds.return_value = 0.0
        mock_word.end_offset.total_seconds.return_value = 1.0
        mock_word.confidence = 0.95
        
        mock_alternative = MagicMock()
        mock_alternative.transcript = "Hello world"
        mock_alternative.confidence = 0.95
        mock_alternative.words = [mock_word]
        
        mock_result = MagicMock()
        mock_result.alternatives = [mock_alternative]
        
        mock_batch_result = MagicMock()
        mock_batch_result.results = [mock_result]
        
        mock_operation_result = MagicMock()
        mock_operation_result.results = [mock_batch_result]
        
        mock_operation = MagicMock()
        mock_operation.result.return_value = mock_operation_result
        
        mock_client_instance = mock_client.return_value
        mock_client_instance.batch_recognize.return_value = mock_operation
        
        provider = GoogleSTTProvider()
        result = provider.transcribe("gs://test-bucket/test.mp3", "zh-TW")
        
        assert isinstance(result, TranscriptionResult)
        assert len(result.segments) >= 1
        assert result.language_code == "zh-TW"
        assert result.cost_usd > 0
    
    @patch('coaching_assistant.services.google_stt.speech_v2.SpeechClient')
    @patch('coaching_assistant.services.google_stt.settings')
    def test_transcribe_with_google_error(self, mock_settings, mock_client):
        """Test transcription with Google API error."""
        from google.api_core import exceptions as gcp_exceptions
        
        mock_settings.GOOGLE_APPLICATION_CREDENTIALS_JSON = ""
        mock_settings.GOOGLE_PROJECT_ID = "test-project"
        
        mock_client_instance = mock_client.return_value
        mock_client_instance.batch_recognize.side_effect = gcp_exceptions.ResourceExhausted("Quota exceeded")
        
        provider = GoogleSTTProvider()
        
        with pytest.raises(Exception):  # Should raise STTProviderQuotaExceededError
            provider.transcribe("gs://test-bucket/test.mp3")
    
    @patch('coaching_assistant.services.google_stt.speech_v2.SpeechClient')
    @patch('coaching_assistant.services.google_stt.settings')
    def test_create_segment_from_words(self, mock_settings, mock_client):
        """Test creating segment from words."""
        mock_settings.GOOGLE_APPLICATION_CREDENTIALS_JSON = ""
        mock_settings.GOOGLE_PROJECT_ID = "test-project"
        
        provider = GoogleSTTProvider()
        
        # Mock words for v2 API
        words = []
        for i, word in enumerate(["Hello", "world"]):
            mock_word = MagicMock()
            mock_word.word = word
            mock_word.start_offset.total_seconds.return_value = float(i)
            mock_word.end_offset.total_seconds.return_value = float(i+1)
            mock_word.confidence = 0.9
            words.append(mock_word)
        
        segment = provider._create_segment_from_words(words, speaker_id=1)
        
        assert segment.speaker_id == 1
        assert segment.content == "Hello world"
        assert segment.start_sec == 0.0
        assert segment.end_sec == 2.0
        assert segment.confidence == 0.9