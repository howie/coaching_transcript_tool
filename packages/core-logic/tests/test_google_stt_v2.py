"""Tests for Google STT v2 API implementation and recent fixes."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from coaching_assistant.services.google_stt import GoogleSTTProvider
from coaching_assistant.services.stt_provider import (
    STTProviderError,
    TranscriptionResult,
    TranscriptSegment
)


class TestGoogleSTTV2Fixes:
    """Test Google STT v2 API specific features and fixes."""
    
    @patch('coaching_assistant.services.google_stt.speech_v2.SpeechClient')
    @patch('coaching_assistant.services.google_stt.settings')
    def test_recognition_features_creation(self, mock_settings, mock_client):
        """Test that RecognitionFeatures object is created correctly."""
        mock_settings.GOOGLE_APPLICATION_CREDENTIALS_JSON = ""
        mock_settings.GOOGLE_PROJECT_ID = "test-project"
        
        provider = GoogleSTTProvider()
        
        # Patch the actual transcribe method components
        with patch('coaching_assistant.services.google_stt.RecognitionFeatures') as mock_features_class, \
             patch('coaching_assistant.services.google_stt.RecognitionConfig') as mock_config_class:
            
            mock_features_instance = MagicMock()
            mock_features_class.return_value = mock_features_instance
            
            mock_config_instance = MagicMock()
            mock_config_class.return_value = mock_config_instance
            
            # Mock successful operation
            mock_operation = MagicMock()
            mock_operation.result.return_value.results = []
            mock_client.return_value.batch_recognize.return_value = mock_operation
            
            # Call transcribe
            try:
                provider.transcribe("gs://test/audio.mp3", "zh-TW", enable_diarization=False)
            except:
                pass  # We're testing the configuration creation, not the full flow
            
            # Verify RecognitionFeatures was created with correct parameters
            mock_features_class.assert_called_once_with(
                enable_automatic_punctuation=True,
                enable_word_time_offsets=True,
                enable_word_confidence=True
            )
    
    @patch('coaching_assistant.services.google_stt.speech_v2.SpeechClient')
    @patch('coaching_assistant.services.google_stt.settings')
    def test_speaker_diarization_config_v2(self, mock_settings, mock_client):
        """Test speaker diarization configuration for v2 API (no enable_speaker_diarization field)."""
        mock_settings.GOOGLE_APPLICATION_CREDENTIALS_JSON = ""
        mock_settings.GOOGLE_PROJECT_ID = "test-project"
        
        provider = GoogleSTTProvider()
        
        with patch('coaching_assistant.services.google_stt.RecognitionFeatures') as mock_features_class, \
             patch('coaching_assistant.services.google_stt.SpeakerDiarizationConfig') as mock_diarization_class, \
             patch('coaching_assistant.services.google_stt.RecognitionConfig') as mock_config_class:
            
            mock_features_instance = MagicMock()
            mock_features_class.return_value = mock_features_instance
            
            mock_diarization_instance = MagicMock()
            mock_diarization_class.return_value = mock_diarization_instance
            
            # Mock successful operation
            mock_operation = MagicMock()
            mock_operation.result.return_value.results = []
            mock_client.return_value.batch_recognize.return_value = mock_operation
            
            # Call transcribe with diarization enabled
            try:
                provider.transcribe("gs://test/audio.mp3", "zh-TW", enable_diarization=True)
            except:
                pass  # We're testing the configuration creation, not the full flow
            
            # Verify SpeakerDiarizationConfig was created with only min/max counts (no enable flag)
            mock_diarization_class.assert_called_once_with(
                min_speaker_count=2,  # Default from settings
                max_speaker_count=4   # Default from settings
            )
            
            # Verify diarization config was assigned to features
            assert mock_features_instance.diarization_config == mock_diarization_instance
    
    @patch('coaching_assistant.services.google_stt.speech_v2.SpeechClient')
    @patch('coaching_assistant.services.google_stt.settings')
    def test_no_diarization_when_disabled(self, mock_settings, mock_client):
        """Test that diarization config is not set when disabled."""
        mock_settings.GOOGLE_APPLICATION_CREDENTIALS_JSON = ""
        mock_settings.GOOGLE_PROJECT_ID = "test-project"
        
        provider = GoogleSTTProvider()
        
        with patch('coaching_assistant.services.google_stt.RecognitionFeatures') as mock_features_class, \
             patch('coaching_assistant.services.google_stt.SpeakerDiarizationConfig') as mock_diarization_class:
            
            mock_features_instance = MagicMock()
            mock_features_class.return_value = mock_features_instance
            
            # Mock successful operation
            mock_operation = MagicMock()
            mock_operation.result.return_value.results = []
            mock_client.return_value.batch_recognize.return_value = mock_operation
            
            # Call transcribe with diarization disabled
            try:
                provider.transcribe("gs://test/audio.mp3", "zh-TW", enable_diarization=False)
            except:
                pass
            
            # Verify SpeakerDiarizationConfig was NOT called
            mock_diarization_class.assert_not_called()
            
            # Verify diarization_config was not assigned
            assert not hasattr(mock_features_instance, 'diarization_config') or \
                   mock_features_instance.diarization_config is None
    
    @patch('coaching_assistant.services.google_stt.speech_v2.SpeechClient')
    @patch('coaching_assistant.services.google_stt.settings')
    def test_base64_credentials_handling(self, mock_settings, mock_client):
        """Test handling of Base64 encoded credentials."""
        import base64
        import json
        
        # Create test credentials
        test_creds = {"type": "service_account", "project_id": "test-project"}
        encoded_creds = base64.b64encode(json.dumps(test_creds).encode()).decode()
        
        mock_settings.GOOGLE_APPLICATION_CREDENTIALS_JSON = encoded_creds
        mock_settings.GOOGLE_PROJECT_ID = "test-project"
        
        with patch('coaching_assistant.services.google_stt.service_account') as mock_service_account:
            mock_credentials = MagicMock()
            mock_service_account.Credentials.from_service_account_info.return_value = mock_credentials
            
            provider = GoogleSTTProvider()
            
            # Verify service account was called with decoded credentials
            mock_service_account.Credentials.from_service_account_info.assert_called_once_with(test_creds)
    
    @patch('coaching_assistant.services.google_stt.speech_v2.SpeechClient')
    @patch('coaching_assistant.services.google_stt.settings')
    def test_raw_json_credentials_handling(self, mock_settings, mock_client):
        """Test handling of raw JSON credentials."""
        import json
        
        test_creds = {"type": "service_account", "project_id": "test-project"}
        raw_json = json.dumps(test_creds)
        
        mock_settings.GOOGLE_APPLICATION_CREDENTIALS_JSON = raw_json
        mock_settings.GOOGLE_PROJECT_ID = "test-project"
        
        with patch('coaching_assistant.services.google_stt.service_account') as mock_service_account:
            mock_credentials = MagicMock()
            mock_service_account.Credentials.from_service_account_info.return_value = mock_credentials
            
            provider = GoogleSTTProvider()
            
            # Verify service account was called with parsed credentials
            mock_service_account.Credentials.from_service_account_info.assert_called_once_with(test_creds)
    
    @patch('coaching_assistant.services.google_stt.speech_v2.SpeechClient')
    @patch('coaching_assistant.services.google_stt.settings')
    def test_invalid_credentials_handling(self, mock_settings, mock_client):
        """Test error handling for invalid credentials."""
        mock_settings.GOOGLE_APPLICATION_CREDENTIALS_JSON = "invalid-json"
        mock_settings.GOOGLE_PROJECT_ID = "test-project"
        
        with pytest.raises(STTProviderError, match="Failed to decode credentials JSON"):
            GoogleSTTProvider()
    
    def test_word_processing_v2_api(self):
        """Test processing words with v2 API format."""
        with patch('coaching_assistant.services.google_stt.speech_v2.SpeechClient'), \
             patch('coaching_assistant.services.google_stt.settings') as mock_settings:
            
            mock_settings.GOOGLE_APPLICATION_CREDENTIALS_JSON = ""
            mock_settings.GOOGLE_PROJECT_ID = "test-project"
            
            provider = GoogleSTTProvider()
            
            # Create mock words in v2 format
            mock_words = []
            for i, word_text in enumerate(["Hello", "world", "test"]):
                mock_word = MagicMock()
                mock_word.word = word_text
                mock_word.start_offset.total_seconds.return_value = float(i)
                mock_word.end_offset.total_seconds.return_value = float(i + 0.5)
                mock_word.confidence = 0.95
                mock_word.speaker_label = "1"
                mock_words.append(mock_word)
            
            # Test segment creation
            segment = provider._create_segment_from_words(mock_words, speaker_id=1)
            
            assert segment.speaker_id == 1
            assert segment.content == "Hello world test"
            assert segment.start_sec == 0.0
            assert segment.end_sec == 2.5  # Last word ends at 2.5
            assert segment.confidence == 0.95


class TestGoogleSTTIntegration:
    """Integration-style tests that verify the complete flow."""
    
    @patch('coaching_assistant.services.google_stt.speech_v2.SpeechClient')
    @patch('coaching_assistant.services.google_stt.settings')
    def test_complete_transcription_flow(self, mock_settings, mock_client):
        """Test complete transcription flow with realistic mock data."""
        mock_settings.GOOGLE_APPLICATION_CREDENTIALS_JSON = ""
        mock_settings.GOOGLE_PROJECT_ID = "test-project"
        
        # Create realistic mock response
        mock_words = []
        sentences = [
            ("Hello", "there,", "how", "are", "you?"),
            ("I'm", "doing", "well,", "thank", "you.")
        ]
        
        word_index = 0
        for speaker_id, sentence in enumerate(sentences, 1):
            for word in sentence:
                mock_word = MagicMock()
                mock_word.word = word
                mock_word.start_offset.total_seconds.return_value = float(word_index * 0.5)
                mock_word.end_offset.total_seconds.return_value = float(word_index * 0.5 + 0.4)
                mock_word.confidence = 0.90 + (word_index * 0.01)
                mock_word.speaker_label = str(speaker_id)
                mock_words.append(mock_word)
                word_index += 1
        
        mock_alternative = MagicMock()
        mock_alternative.transcript = "Hello there, how are you? I'm doing well, thank you."
        mock_alternative.confidence = 0.95
        mock_alternative.words = mock_words
        
        mock_result = MagicMock()
        mock_result.alternatives = [mock_alternative]
        
        mock_batch_result = MagicMock()
        mock_batch_result.results = [mock_result]
        
        mock_operation_result = MagicMock()
        mock_operation_result.results = [mock_batch_result]
        
        mock_operation = MagicMock()
        mock_operation.result.return_value = mock_operation_result
        
        mock_client.return_value.batch_recognize.return_value = mock_operation
        
        # Execute transcription
        provider = GoogleSTTProvider()
        result = provider.transcribe("gs://test-bucket/test.m4a", "zh-TW", enable_diarization=True)
        
        # Verify result structure
        assert isinstance(result, TranscriptionResult)
        assert result.language_code == "zh-TW"
        assert result.cost_usd > 0
        assert len(result.segments) >= 2  # Should have segments from both speakers
        
        # Verify segments have different speakers
        speaker_ids = {segment.speaker_id for segment in result.segments}
        assert len(speaker_ids) >= 2
        
        # Verify segment content
        for segment in result.segments:
            assert isinstance(segment, TranscriptSegment)
            assert len(segment.content.strip()) > 0
            assert segment.start_sec >= 0
            assert segment.end_sec > segment.start_sec
            assert 0.0 <= segment.confidence <= 1.0