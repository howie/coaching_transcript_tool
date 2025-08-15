"""Unit tests for AssemblyAI STT provider."""

import pytest
import json
from unittest.mock import Mock, patch, mock_open
from decimal import Decimal
from uuid import uuid4

from coaching_assistant.services.assemblyai_stt import (
    AssemblyAIProvider,
    ASSEMBLYAI_LANGUAGE_MAP,
    NEEDS_TRADITIONAL_CONVERSION,
)
from coaching_assistant.services.stt_provider import (
    TranscriptSegment,
    STTProviderError,
    STTProviderUnavailableError,
    STTProviderQuotaExceededError,
    STTProviderInvalidAudioError,
)


class TestAssemblyAIProvider:
    """Test AssemblyAI provider initialization and configuration."""

    def test_init_with_api_key(self):
        """Test successful initialization with API key."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-api-key"
            mock_settings.ASSEMBLYAI_MODEL = "best"
            mock_settings.ASSEMBLYAI_SPEAKERS_EXPECTED = 2

            provider = AssemblyAIProvider()

            assert provider.api_key == "test-api-key"
            assert provider.model == "best"
            assert provider.speakers_expected == 2
            assert provider.provider_name == "assemblyai"

    def test_init_without_api_key(self):
        """Test initialization failure without API key."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = ""

            with pytest.raises(STTProviderError, match="ASSEMBLYAI_API_KEY is not set"):
                AssemblyAIProvider()

    def test_language_code_mapping(self):
        """Test language code mapping functionality."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            provider = AssemblyAIProvider()

            # Test specific mappings
            assert provider._map_language_code("cmn-Hant-TW") == "zh"
            assert provider._map_language_code("zh-TW") == "zh"
            assert provider._map_language_code("en-US") == "en"
            assert provider._map_language_code("ja-JP") == "ja"
            assert provider._map_language_code("auto") is None

    def test_traditional_conversion_check(self):
        """Test Traditional Chinese conversion requirement check."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            provider = AssemblyAIProvider()

            assert provider._needs_traditional_conversion("cmn-Hant-TW") is True
            assert provider._needs_traditional_conversion("zh-TW") is True
            assert provider._needs_traditional_conversion("zh-CN") is False
            assert provider._needs_traditional_conversion("en-US") is False

    def test_speaker_id_conversion(self):
        """Test speaker ID conversion from AssemblyAI strings to integers."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            provider = AssemblyAIProvider()

            # Test string to integer conversion
            assert provider._convert_speaker_id("A") == 1
            assert provider._convert_speaker_id("B") == 2
            assert provider._convert_speaker_id("C") == 3
            assert provider._convert_speaker_id("a") == 1  # lowercase should work
            assert provider._convert_speaker_id("b") == 2

            # Test integer passthrough (0 gets converted to 1, others stay the same)
            assert provider._convert_speaker_id(0) == 1  # 0 -> 1 conversion
            assert provider._convert_speaker_id(1) == 1  # stays 1
            assert provider._convert_speaker_id(2) == 2  # stays 2

            # Test invalid inputs (fallback to 1)
            assert provider._convert_speaker_id("invalid") == 1
            assert provider._convert_speaker_id(None) == 1
            assert provider._convert_speaker_id([]) == 1


class TestChineseTextProcessing:
    """Test Chinese text processing functionality."""

    def test_chinese_text_processing_simplified(self):
        """Test Chinese text processing without Traditional conversion."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            provider = AssemblyAIProvider()

            text = "你 好 吗 ？"
            result = provider._process_chinese_text(text, needs_conversion=False)

            # Should remove spaces between Chinese characters
            assert result == "你好吗？"

    @patch("coaching_assistant.services.assemblyai_stt.convert_to_traditional")
    def test_chinese_text_processing_traditional(self, mock_convert):
        """Test Chinese text processing with Traditional conversion."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            provider = AssemblyAIProvider()

            mock_convert.return_value = "你好嗎？"

            text = "你 好 吗 ？"
            result = provider._process_chinese_text(text, needs_conversion=True)

            mock_convert.assert_called_once()
            assert result == "你好嗎？"

    def test_punctuation_spacing_fix(self):
        """Test punctuation spacing fixes."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            provider = AssemblyAIProvider()

            text = "你好 ， 今天怎麼樣 ？"
            result = provider._process_chinese_text(text, needs_conversion=False)

            assert result == "你好，今天怎麼樣？"


class TestAudioUpload:
    """Test audio upload functionality."""

    def test_upload_http_url_direct(self):
        """Test direct HTTP URL usage."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            provider = AssemblyAIProvider()

            url = "https://example.com/audio.mp3"
            result = provider._upload_audio(url)
            assert result == url

    def test_upload_gcs_uri_invalid_format(self):
        """Test GCS URI handling with invalid format."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            provider = AssemblyAIProvider()

            # Test invalid GCS URI (missing path)
            with pytest.raises(STTProviderError, match="Invalid GCS URI format"):
                provider._upload_audio("gs://bucket-only")

    @patch("coaching_assistant.services.assemblyai_stt.requests.post")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake audio data")
    def test_upload_local_file(self, mock_file, mock_post):
        """Test local file upload."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            provider = AssemblyAIProvider()

            mock_response = Mock()
            mock_response.json.return_value = {
                "upload_url": "https://cdn.assemblyai.com/upload/abc123"
            }
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            result = provider._upload_audio("/path/to/audio.mp3")

            assert result == "https://cdn.assemblyai.com/upload/abc123"
            mock_post.assert_called_once()
            mock_file.assert_called_once()


class TestTranscriptionSubmission:
    """Test transcription job submission."""

    @patch("coaching_assistant.services.assemblyai_stt.requests.post")
    def test_submit_transcription_basic(self, mock_post):
        """Test basic transcription submission."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            mock_settings.ASSEMBLYAI_MODEL = "best"
            provider = AssemblyAIProvider()

            mock_response = Mock()
            mock_response.json.return_value = {"id": "transcript_123"}
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            result = provider._submit_transcription(
                "https://example.com/audio.mp3", "zh", True, 2
            )

            assert result == "transcript_123"
            mock_post.assert_called_once()

            # Verify request payload
            call_args = mock_post.call_args
            assert call_args[1]["json"]["audio_url"] == "https://example.com/audio.mp3"
            assert call_args[1]["json"]["language_code"] == "zh"
            assert call_args[1]["json"]["speaker_labels"] is True
            assert call_args[1]["json"]["speakers_expected"] == 2

    @patch("coaching_assistant.services.assemblyai_stt.requests.post")
    def test_submit_transcription_rate_limit(self, mock_post):
        """Test rate limit error handling."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            provider = AssemblyAIProvider()

            mock_response = Mock()
            mock_response.status_code = 429
            mock_post.return_value = mock_response

            # Create an HTTPError with the proper response
            from requests.exceptions import HTTPError

            http_error = HTTPError("Rate limit exceeded")
            http_error.response = mock_response
            mock_post.return_value.raise_for_status.side_effect = http_error

            with pytest.raises(STTProviderQuotaExceededError):
                provider._submit_transcription("url", None, False, 2)


class TestTranscriptionPolling:
    """Test transcription status polling."""

    @patch("coaching_assistant.services.assemblyai_stt.requests.get")
    @patch("coaching_assistant.services.assemblyai_stt.time.sleep")
    def test_poll_completed_successfully(self, mock_sleep, mock_get):
        """Test successful polling completion."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            provider = AssemblyAIProvider()

            # First call: processing, second call: completed
            responses = [
                Mock(json=lambda: {"status": "processing"}),
                Mock(json=lambda: {"status": "completed", "text": "Hello world"}),
            ]
            for resp in responses:
                resp.raise_for_status = Mock()
            mock_get.side_effect = responses

            result = provider._poll_transcription_status("transcript_123")

            assert result["status"] == "completed"
            assert result["text"] == "Hello world"
            assert mock_get.call_count == 2
            assert mock_sleep.call_count == 1

    @patch("coaching_assistant.services.assemblyai_stt.requests.get")
    def test_poll_error_status(self, mock_get):
        """Test error status handling."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            provider = AssemblyAIProvider()

            mock_response = Mock()
            mock_response.json.return_value = {
                "status": "error",
                "error": "Audio too short",
            }
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            with pytest.raises(
                STTProviderError, match="Transcription failed: Audio too short"
            ):
                provider._poll_transcription_status("transcript_123")


class TestResultParsing:
    """Test transcript result parsing."""

    def test_parse_utterances_result(self):
        """Test parsing result with utterances (speaker diarization)."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            mock_settings.ASSEMBLYAI_SPEAKERS_EXPECTED = 2
            provider = AssemblyAIProvider()

            result = {
                "id": "transcript_123",
                "language_code": "en",
                "confidence": 0.95,
                "audio_duration": 30000,  # 30 seconds in ms
                "utterances": [
                    {
                        "speaker": "A",  # AssemblyAI uses string speaker IDs
                        "start": 1000,  # 1 second
                        "end": 3000,  # 3 seconds
                        "text": "Hello, how are you today?",
                        "confidence": 0.9,
                    },
                    {
                        "speaker": "B",  # AssemblyAI uses string speaker IDs
                        "start": 3500,
                        "end": 6000,
                        "text": "I'm doing well, thank you.",
                        "confidence": 0.85,
                    },
                ],
            }

            with patch(
                "coaching_assistant.services.assemblyai_stt.assign_roles_simple"
            ) as mock_assign:
                mock_assign.return_value = (
                    {1: "coach", 2: "client"},
                    {"confidence": 0.8},
                )

                parsed = provider._parse_transcript_result(result, "en-US", True)

                assert len(parsed.segments) == 2
                assert parsed.segments[0].speaker_id == 1
                assert parsed.segments[0].start_seconds == 1.0
                assert parsed.segments[0].end_seconds == 3.0
                assert parsed.segments[0].content == "Hello, how are you today?"
                assert parsed.segments[0].confidence == 0.9

                assert parsed.total_duration_sec == 30.0
                assert parsed.language_code == "en"
                assert parsed.provider_metadata["provider"] == "assemblyai"
                assert parsed.provider_metadata["speaker_role_assignments"] == {
                    1: "coach",
                    2: "client",
                }

    def test_parse_chinese_result_with_conversion(self):
        """Test parsing Chinese result with Traditional conversion."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            provider = AssemblyAIProvider()

            result = {
                "id": "transcript_456",
                "language_code": "zh",
                "confidence": 0.92,
                "audio_duration": 15000,
                "utterances": [
                    {
                        "speaker": "A",  # AssemblyAI uses string speaker IDs
                        "start": 0,
                        "end": 5000,
                        "text": "你 好 吗 ？",
                        "confidence": 0.88,
                    }
                ],
            }

            with patch.object(provider, "_process_chinese_text") as mock_process:
                mock_process.return_value = "你好嗎？"

                parsed = provider._parse_transcript_result(result, "zh-TW", False)

                mock_process.assert_called_once_with("你 好 吗 ？", True)
                assert parsed.segments[0].content == "你好嗎？"
                assert parsed.provider_metadata["post_processing_applied"] == [
                    "remove_spaces",
                    "convert_to_traditional",
                ]

    def test_parse_no_utterances_fallback(self):
        """Test parsing when no utterances are available."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            provider = AssemblyAIProvider()

            result = {
                "id": "transcript_789",
                "language_code": "en",
                "confidence": 0.9,
                "audio_duration": 10000,
                "text": "This is the full transcript text.",
                "words": [
                    {"text": "This", "start": 0, "end": 500, "confidence": 0.95},
                    {"text": "is", "start": 500, "end": 750, "confidence": 0.9},
                    {"text": "the", "start": 750, "end": 1000, "confidence": 0.85},
                    {"text": "full", "start": 1000, "end": 1500, "confidence": 0.92},
                    {
                        "text": "transcript.",
                        "start": 1500,
                        "end": 2500,
                        "confidence": 0.88,
                    },
                    {"text": "text.", "start": 2500, "end": 3000, "confidence": 0.9},
                ],
            }

            parsed = provider._parse_transcript_result(result, "en-US", False)

            # Should create segments based on sentence endings
            assert len(parsed.segments) >= 1
            assert "transcript." in parsed.segments[0].content


class TestCostEstimation:
    """Test cost estimation functionality."""

    def test_estimate_cost_best_model(self):
        """Test cost estimation for best model."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            mock_settings.ASSEMBLYAI_MODEL = "best"
            provider = AssemblyAIProvider()

            # 28 minutes = 1680 seconds
            cost = provider.estimate_cost(1680)
            expected = Decimal("0.00025") * 1680  # $0.42

            assert cost == expected
            assert float(cost) == 0.42

    def test_estimate_cost_nano_model(self):
        """Test cost estimation for nano model."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            mock_settings.ASSEMBLYAI_MODEL = "nano"
            provider = AssemblyAIProvider()

            # 28 minutes = 1680 seconds
            cost = provider.estimate_cost(1680)
            expected = Decimal("0.000125") * 1680  # $0.21

            assert cost == expected
            assert float(cost) == 0.21


class TestFullTranscriptionWorkflow:
    """Test complete transcription workflow."""

    @patch("coaching_assistant.services.assemblyai_stt.assign_roles_simple")
    @patch("coaching_assistant.services.assemblyai_stt.requests.get")
    @patch("coaching_assistant.services.assemblyai_stt.requests.post")
    @patch("coaching_assistant.services.assemblyai_stt.time.sleep")
    def test_complete_transcription_workflow(
        self, mock_sleep, mock_post, mock_get, mock_assign
    ):
        """Test complete transcription from start to finish."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            mock_settings.ASSEMBLYAI_MODEL = "best"
            mock_settings.ASSEMBLYAI_SPEAKERS_EXPECTED = 2
            provider = AssemblyAIProvider()

            # Mock submission response
            submit_response = Mock()
            submit_response.json.return_value = {"id": "transcript_abc"}
            submit_response.raise_for_status = Mock()
            mock_post.return_value = submit_response

            # Mock polling responses (processing -> completed)
            poll_responses = [
                Mock(json=lambda: {"status": "processing"}),
                Mock(
                    json=lambda: {
                        "status": "completed",
                        "id": "transcript_abc",
                        "language_code": "en",
                        "confidence": 0.9,
                        "audio_duration": 15000,
                        "utterances": [
                            {
                                "speaker": "A",  # AssemblyAI uses string speaker IDs
                                "start": 1000,
                                "end": 5000,
                                "text": "How are you feeling today?",
                                "confidence": 0.95,
                            },
                            {
                                "speaker": "B",  # AssemblyAI uses string speaker IDs
                                "start": 6000,
                                "end": 12000,
                                "text": "I'm feeling quite overwhelmed with work lately.",
                                "confidence": 0.88,
                            },
                        ],
                    }
                ),
            ]
            for resp in poll_responses:
                resp.raise_for_status = Mock()
            mock_get.side_effect = poll_responses

            # Mock role assignment
            mock_assign.return_value = ({1: "coach", 2: "client"}, {"confidence": 0.85})

            # Execute transcription
            result = provider.transcribe(
                audio_uri="https://example.com/coaching.mp3",
                language="en-US",
                enable_diarization=True,
            )

            # Verify results
            assert len(result.segments) == 2
            assert result.segments[0].content == "How are you feeling today?"
            assert (
                result.segments[1].content
                == "I'm feeling quite overwhelmed with work lately."
            )
            assert result.total_duration_sec == 15.0
            assert result.language_code == "en"
            assert result.provider_metadata["provider"] == "assemblyai"
            assert result.provider_metadata["speaker_role_assignments"] == {
                1: "coach",
                2: "client",
            }
            assert result.provider_metadata["automatic_role_assignment"] is True

            # Verify API calls
            mock_post.assert_called_once()
            mock_get.call_count == 2
            mock_assign.assert_called_once()


class TestErrorHandling:
    """Test comprehensive error handling."""

    @patch("coaching_assistant.services.assemblyai_stt.requests.post")
    def test_transcription_http_errors(self, mock_post):
        """Test various HTTP error scenarios."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            provider = AssemblyAIProvider()

            from requests.exceptions import HTTPError

            # Test 400 Bad Request
            mock_response = Mock()
            mock_response.status_code = 400
            http_error = HTTPError("Bad request")
            http_error.response = mock_response
            mock_post.return_value = mock_response
            mock_post.return_value.raise_for_status.side_effect = http_error

            with pytest.raises(STTProviderInvalidAudioError):
                provider._submit_transcription("url", "en", False, 2)

            # Test 429 Rate Limit
            mock_response.status_code = 429
            http_error = HTTPError("Rate limit")
            http_error.response = mock_response
            mock_post.return_value.raise_for_status.side_effect = http_error

            with pytest.raises(STTProviderQuotaExceededError):
                provider._submit_transcription("url", "en", False, 2)

            # Test 500 Server Error
            mock_response.status_code = 500
            http_error = HTTPError("Server error")
            http_error.response = mock_response
            mock_post.return_value.raise_for_status.side_effect = http_error

            with pytest.raises(STTProviderError):
                provider._submit_transcription("url", "en", False, 2)

    @patch("coaching_assistant.services.assemblyai_stt.requests.get")
    @patch("coaching_assistant.services.assemblyai_stt.time.sleep")
    def test_polling_timeout(self, mock_sleep, mock_get):
        """Test polling timeout handling."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            provider = AssemblyAIProvider()

            # Always return processing status
            mock_response = Mock()
            mock_response.json.return_value = {"status": "processing"}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            with pytest.raises(STTProviderError, match="Transcription timed out"):
                provider._poll_transcription_status("transcript_123")

    def test_invalid_audio_file_upload(self):
        """Test handling of invalid audio file paths."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            provider = AssemblyAIProvider()

            with patch(
                "builtins.open", side_effect=FileNotFoundError("File not found")
            ):
                with pytest.raises(STTProviderError, match="Failed to upload audio"):
                    provider._upload_audio("/nonexistent/file.mp3")


class TestGCSIntegration:
    """Test GCS URI handling."""

    @patch("coaching_assistant.utils.gcs_uploader.GCSUploader")
    def test_gcs_uri_to_signed_url(self, mock_gcs_uploader_class):
        """Test conversion of GCS URI to signed URL."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            mock_settings.GOOGLE_APPLICATION_CREDENTIALS_JSON = "fake-creds"

            # Mock GCSUploader instance
            mock_uploader = Mock()
            mock_uploader.generate_signed_read_url.return_value = (
                "https://storage.googleapis.com/bucket/path?signed"
            )
            mock_gcs_uploader_class.return_value = mock_uploader

            provider = AssemblyAIProvider()

            # Test GCS URI conversion
            gcs_uri = "gs://my-bucket/path/to/audio.mp3"
            result = provider._upload_audio(gcs_uri)

            # Verify signed URL returned
            assert result == "https://storage.googleapis.com/bucket/path?signed"

            # Verify GCS uploader was created correctly
            mock_gcs_uploader_class.assert_called_once()
            call_args = mock_gcs_uploader_class.call_args
            assert call_args.kwargs["bucket_name"] == "my-bucket"
            assert "credentials_json" in call_args.kwargs  # Just verify it exists

            # Verify signed URL was generated
            mock_uploader.generate_signed_read_url.assert_called_once_with(
                blob_name="path/to/audio.mp3", expiration_minutes=120
            )

    def test_gcs_uri_invalid_format(self):
        """Test handling of invalid GCS URI format."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"
            provider = AssemblyAIProvider()

            # Test invalid GCS URI (missing path)
            with pytest.raises(STTProviderError, match="Invalid GCS URI format"):
                provider._upload_audio("gs://bucket-only")

    @patch("coaching_assistant.utils.gcs_uploader.GCSUploader")
    def test_gcs_uri_uploader_error(self, mock_gcs_uploader_class):
        """Test error handling when GCS uploader fails."""
        with patch(
            "coaching_assistant.services.assemblyai_stt.settings"
        ) as mock_settings:
            mock_settings.ASSEMBLYAI_API_KEY = "test-key"

            # Mock GCS uploader to raise exception
            mock_gcs_uploader_class.side_effect = Exception("GCS credentials error")

            provider = AssemblyAIProvider()

            with pytest.raises(
                STTProviderError, match="Failed to convert GCS URI to signed URL"
            ):
                provider._upload_audio("gs://bucket/path/file.mp3")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
