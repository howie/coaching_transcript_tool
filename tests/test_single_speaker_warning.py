"""Test single speaker detection warning functionality."""

import logging
from unittest.mock import patch, Mock
import pytest
from coaching_assistant.services.assemblyai_stt import AssemblyAIProvider


class TestSingleSpeakerWarning:
    """Test single speaker detection and warnings."""
    
    def test_single_speaker_detection_warning(self, caplog):
        """Test that warning is logged when only one speaker is detected."""
        with patch('coaching_assistant.services.assemblyai_stt.settings') as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            mock_settings.ASSEMBLYAI_SPEAKERS_EXPECTED = 2
            provider = AssemblyAIProvider()
            
            # Mock result with only one speaker
            result = {
                "id": "transcript_123",
                "language_code": "en",
                "confidence": 0.95,
                "audio_duration": 30000,
                "utterances": [
                    {
                        "speaker": "A",  # Only one speaker
                        "start": 1000,
                        "end": 5000,
                        "text": "This is a monologue with only one speaker.",
                        "confidence": 0.9
                    },
                    {
                        "speaker": "A",  # Same speaker continues
                        "start": 6000,
                        "end": 10000,
                        "text": "There is no second person in this conversation.",
                        "confidence": 0.85
                    }
                ]
            }
            
            # Set logging level to capture warnings
            with caplog.at_level(logging.WARNING):
                parsed = provider._parse_transcript_result(result, "en-US", True)
            
            # Verify single speaker was detected
            assert len(parsed.segments) == 2
            assert parsed.segments[0].speaker_id == 1
            assert parsed.segments[1].speaker_id == 1  # Same speaker
            
            # Verify warning was logged
            warning_messages = [record.message for record in caplog.records if record.levelname == 'WARNING']
            assert len(warning_messages) == 2  # Should have 2 warning messages
            
            # Check for speaker mismatch warning
            mismatch_warning = next((msg for msg in warning_messages 
                                   if "Speaker diarization mismatch" in msg), None)
            assert mismatch_warning is not None
            assert "expected 2 speakers, but only detected 1 speaker" in mismatch_warning
            
            # Check for role assignment warning
            role_warning = next((msg for msg in warning_messages 
                               if "Cannot assign coach/client roles" in msg), None)
            assert role_warning is not None
            assert "only 1 speaker detected" in role_warning
            assert "Manual role assignment may be required" in role_warning
            
            # Verify provider metadata includes the mismatch information
            metadata = parsed.provider_metadata
            assert metadata["speakers_expected"] == 2
            assert metadata["speakers_detected"] == 1
            assert metadata["speakers_detected_ids"] == [1]
            assert metadata["speaker_diarization_mismatch"] is True
            assert metadata["automatic_role_assignment"] is False
            assert metadata["speaker_role_assignments"] == {}
    
    def test_more_speakers_than_expected_info(self, caplog):
        """Test that info is logged when more speakers than expected are detected."""
        with patch('coaching_assistant.services.assemblyai_stt.settings') as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            mock_settings.ASSEMBLYAI_SPEAKERS_EXPECTED = 2
            provider = AssemblyAIProvider()
            
            # Mock result with three speakers (more than expected 2)
            result = {
                "id": "transcript_123",
                "language_code": "en",
                "confidence": 0.95,
                "audio_duration": 30000,
                "utterances": [
                    {"speaker": "A", "start": 1000, "end": 3000, "text": "Speaker A", "confidence": 0.9},
                    {"speaker": "B", "start": 3500, "end": 6000, "text": "Speaker B", "confidence": 0.85},
                    {"speaker": "C", "start": 6500, "end": 9000, "text": "Speaker C", "confidence": 0.8},
                ]
            }
            
            with patch('coaching_assistant.services.assemblyai_stt.assign_roles_simple') as mock_assign:
                mock_assign.return_value = ({1: 'coach', 2: 'client', 3: 'observer'}, {'confidence': 0.7})
                
                with caplog.at_level(logging.INFO):
                    parsed = provider._parse_transcript_result(result, "en-US", True)
            
            # Verify three speakers were detected
            assert len(parsed.segments) == 3
            unique_speakers = set(s.speaker_id for s in parsed.segments)
            assert unique_speakers == {1, 2, 3}
            
            # Check for info message about more speakers than expected
            info_messages = [record.message for record in caplog.records if record.levelname == 'INFO']
            more_speakers_info = next((msg for msg in info_messages 
                                     if "detected more speakers than expected" in msg), None)
            assert more_speakers_info is not None
            assert "expected 2, detected 3" in more_speakers_info
            
            # Verify provider metadata
            metadata = parsed.provider_metadata
            assert metadata["speakers_expected"] == 2
            assert metadata["speakers_detected"] == 3
            assert metadata["speakers_detected_ids"] == [1, 2, 3]
            assert metadata["speaker_diarization_mismatch"] is True
            assert metadata["automatic_role_assignment"] is True
    
    def test_expected_speakers_count_matches(self, caplog):
        """Test normal case where detected speakers match expected count."""
        with patch('coaching_assistant.services.assemblyai_stt.settings') as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            mock_settings.ASSEMBLYAI_SPEAKERS_EXPECTED = 2
            provider = AssemblyAIProvider()
            
            # Mock result with exactly 2 speakers (matches expected)
            result = {
                "id": "transcript_123",
                "language_code": "en",
                "confidence": 0.95,
                "audio_duration": 30000,
                "utterances": [
                    {"speaker": "A", "start": 1000, "end": 3000, "text": "Coach speaking", "confidence": 0.9},
                    {"speaker": "B", "start": 3500, "end": 6000, "text": "Client speaking", "confidence": 0.85},
                ]
            }
            
            with patch('coaching_assistant.services.assemblyai_stt.assign_roles_simple') as mock_assign:
                mock_assign.return_value = ({1: 'coach', 2: 'client'}, {'confidence': 0.85})
                
                with caplog.at_level(logging.WARNING):
                    parsed = provider._parse_transcript_result(result, "en-US", True)
            
            # Verify two speakers were detected
            assert len(parsed.segments) == 2
            unique_speakers = set(s.speaker_id for s in parsed.segments)
            assert unique_speakers == {1, 2}
            
            # Should not have any warning messages about speaker count mismatch
            warning_messages = [record.message for record in caplog.records if record.levelname == 'WARNING']
            mismatch_warnings = [msg for msg in warning_messages if "Speaker diarization mismatch" in msg]
            assert len(mismatch_warnings) == 0
            
            # Verify provider metadata shows no mismatch
            metadata = parsed.provider_metadata
            assert metadata["speakers_expected"] == 2
            assert metadata["speakers_detected"] == 2
            assert metadata["speakers_detected_ids"] == [1, 2]
            assert metadata["speaker_diarization_mismatch"] is False
            assert metadata["automatic_role_assignment"] is True