"""AssemblyAI Speech-to-Text provider implementation."""

import re
import time
import logging
import requests
from decimal import Decimal
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from .stt_provider import (
    STTProvider,
    TranscriptSegment,
    TranscriptionResult,
    STTProviderError,
    STTProviderUnavailableError,
    STTProviderQuotaExceededError,
    STTProviderInvalidAudioError,
)
from ..core.config import settings
from ..utils.chinese_converter import convert_to_traditional
from ..utils.simple_role_assigner import assign_roles_simple

logger = logging.getLogger(__name__)


# AssemblyAI language code mapping
ASSEMBLYAI_LANGUAGE_MAP = {
    "cmn-Hant-TW": "zh",  # Map Traditional Chinese to Simplified (with post-processing)
    "zh-TW": "zh",  # Map to 'zh' + post-process to Traditional
    "cmn-Hans-CN": "zh",  # Simplified Chinese (native support)
    "zh-CN": "zh",  # Simplified Chinese (native support)
    "en-US": "en",  # English
    "en": "en",  # English
    "ja": "ja",  # Japanese
    "ja-JP": "ja",  # Japanese
}

# Languages that need Traditional Chinese conversion
NEEDS_TRADITIONAL_CONVERSION = ["cmn-Hant-TW", "zh-TW"]


class AssemblyAIProvider(STTProvider):
    """AssemblyAI Speech-to-Text provider implementation."""

    BASE_URL = "https://api.assemblyai.com/v2"

    def __init__(self):
        """Initialize AssemblyAI client."""
        self.api_key = settings.ASSEMBLYAI_API_KEY
        if not self.api_key:
            raise STTProviderError("ASSEMBLYAI_API_KEY is not set in configuration")

        self.headers = {
            "authorization": self.api_key,
            "content-type": "application/json",
        }

        # Model selection (best or nano)
        self.model = getattr(settings, "ASSEMBLYAI_MODEL", "best")
        self.speakers_expected = getattr(settings, "ASSEMBLYAI_SPEAKERS_EXPECTED", 2)

        logger.info(f"AssemblyAI provider initialized with model: {self.model}")

    def _map_language_code(self, language: str) -> str:
        """Map input language code to AssemblyAI language code."""
        if not language or language == "auto":
            return None  # Let AssemblyAI auto-detect

        # Map to AssemblyAI language code
        mapped_code = ASSEMBLYAI_LANGUAGE_MAP.get(language, language)
        logger.debug(f"Mapped language '{language}' to AssemblyAI code '{mapped_code}'")
        return mapped_code

    def _needs_traditional_conversion(self, language: str) -> bool:
        """Check if the language needs Traditional Chinese conversion."""
        return language in NEEDS_TRADITIONAL_CONVERSION

    def _convert_speaker_id(self, speaker_id) -> int:
        """Convert AssemblyAI speaker ID to integer.

        AssemblyAI returns speaker IDs as strings ("A", "B", "C", etc.)
        but our database expects integers starting from 1 (1, 2, 3, etc.).
        This matches our frontend/backend convention where 1=coach, 2=client.
        """
        if isinstance(speaker_id, int):
            # If already an integer, ensure it's at least 1
            return max(1, speaker_id + 1) if speaker_id == 0 else speaker_id

        if isinstance(speaker_id, str):
            # Convert "A" -> 1, "B" -> 2, "C" -> 3, etc.
            try:
                return ord(speaker_id.upper()) - ord("A") + 1
            except (ValueError, TypeError):
                logger.warning(
                    f"Failed to convert speaker ID '{speaker_id}' to integer, defaulting to 1"
                )
                return 1

        # Fallback for any other type
        logger.warning(
            f"Unexpected speaker ID type: {type(speaker_id)}, value: {speaker_id}, defaulting to 1"
        )
        return 1

    def _process_chinese_text(self, text: str, needs_conversion: bool) -> str:
        """Post-process Chinese transcription from AssemblyAI."""
        # Remove spaces between Chinese characters and around punctuation
        text = re.sub(
            r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff，。！？；：、）】」』（【「『])",
            "",
            text,
        )
        text = re.sub(
            r"(?<=[，。！？；：、）】」』（【「『])\s+(?=[\u4e00-\u9fff])", "", text
        )

        # Convert to Traditional Chinese if needed
        if needs_conversion:
            text = convert_to_traditional(text)
            logger.debug("Converted text to Traditional Chinese")

        # Final cleanup: remove any remaining spaces around Chinese punctuation
        text = re.sub(r"\s+([，。！？；：、）】」』])", r"\1", text)
        text = re.sub(r"([（【「『])\s+", r"\1", text)

        return text

    def _upload_audio(self, audio_uri: str) -> str:
        """Upload audio file to AssemblyAI or return URL if already accessible."""
        # If it's already an HTTP/HTTPS URL, return it directly
        if audio_uri.startswith(("http://", "https://")):
            logger.info(f"Using direct URL for AssemblyAI: {audio_uri}")
            return audio_uri

        # If it's a GCS URI, convert it to a signed URL
        if audio_uri.startswith("gs://"):
            logger.info(f"Converting GCS URI to signed URL: {audio_uri}")

            try:
                # Extract bucket and blob name from GCS URI
                # Format: gs://bucket-name/path/to/file.ext
                gcs_parts = audio_uri.replace("gs://", "").split("/", 1)
                if len(gcs_parts) != 2:
                    raise STTProviderError(f"Invalid GCS URI format: {audio_uri}")

                bucket_name, blob_name = gcs_parts

                # Import GCSUploader here to avoid circular imports
                from ..utils.gcs_uploader import GCSUploader
                from ..core.config import settings

                # Create GCS uploader with the same bucket and credentials
                uploader = GCSUploader(
                    bucket_name=bucket_name,
                    credentials_json=settings.GOOGLE_APPLICATION_CREDENTIALS_JSON,
                )

                # Generate signed read URL (valid for 6 hours for transcription + retries)
                signed_url = uploader.generate_signed_read_url(
                    blob_name=blob_name,
                    expiration_minutes=360,  # 6 hours to handle retries and long transcriptions
                )

                logger.info(
                    f"✅ Generated signed URL for AssemblyAI: {signed_url[:60]}..."
                )
                return signed_url

            except Exception as e:
                logger.error(f"Failed to generate signed URL from GCS URI: {e}")
                raise STTProviderError(f"Failed to convert GCS URI to signed URL: {e}")

        # If it's a local file path, upload it to AssemblyAI
        logger.info(f"Uploading local file to AssemblyAI: {audio_uri}")
        upload_url = f"{self.BASE_URL}/upload"

        try:
            with open(audio_uri, "rb") as f:
                response = requests.post(
                    upload_url,
                    headers={"authorization": self.api_key},
                    files={"file": f},
                )
                response.raise_for_status()
                upload_response = response.json()
                return upload_response["upload_url"]
        except Exception as e:
            logger.error(f"Failed to upload audio file: {e}")
            raise STTProviderError(f"Failed to upload audio: {e}")

    def _submit_transcription(
        self,
        audio_url: str,
        language_code: Optional[str],
        enable_diarization: bool,
        speakers_expected: int,
    ) -> str:
        """Submit transcription job to AssemblyAI."""
        transcript_request = {
            "audio_url": audio_url,
            "speech_model": self.model,
        }

        # Add language if specified
        if language_code:
            transcript_request["language_code"] = language_code

        # Enable speaker diarization if requested
        if enable_diarization:
            transcript_request["speaker_labels"] = True
            transcript_request["speakers_expected"] = speakers_expected

        # Enable additional features for better accuracy
        transcript_request["punctuate"] = True
        transcript_request["format_text"] = True

        logger.info(f"Submitting transcription request: {transcript_request}")

        try:
            response = requests.post(
                f"{self.BASE_URL}/transcript",
                json=transcript_request,
                headers=self.headers,
            )
            response.raise_for_status()
            transcript_response = response.json()
            return transcript_response["id"]
        except requests.exceptions.HTTPError as e:
            status_code = getattr(e.response, "status_code", None)
            if status_code == 429:
                raise STTProviderQuotaExceededError("AssemblyAI rate limit exceeded")
            elif status_code == 400:
                raise STTProviderInvalidAudioError(f"Invalid audio or request: {e}")
            else:
                raise STTProviderError(f"Failed to submit transcription: {e}")
        except Exception as e:
            # Check if this is an HTTPError-like exception with a status_code
            if hasattr(e, "response") and hasattr(e.response, "status_code"):
                status_code = e.response.status_code
                if status_code == 429:
                    raise STTProviderQuotaExceededError(
                        "AssemblyAI rate limit exceeded"
                    )
                elif status_code == 400:
                    raise STTProviderInvalidAudioError(f"Invalid audio or request: {e}")

            logger.error(f"Failed to submit transcription: {e}")
            raise STTProviderError(f"Failed to submit transcription: {e}")

    def _poll_transcription_status(
        self, transcript_id: str, progress_callback=None
    ) -> Dict[str, Any]:
        """Poll for transcription completion with optional progress updates."""
        polling_url = f"{self.BASE_URL}/transcript/{transcript_id}"
        polling_interval = 30  # Poll every 30 seconds (reduced from 1 second)
        max_retries = 240  # Max 2 hours (240 * 30 seconds = 7200 seconds = 2 hours)
        retry_count = 0
        start_time = time.time()

        logger.info(
            f"Polling transcription status for ID: {transcript_id} (every {polling_interval}s)"
        )

        while retry_count < max_retries:
            try:
                response = requests.get(polling_url, headers=self.headers)
                response.raise_for_status()
                result = response.json()

                status = result["status"]
                logger.debug(f"Transcription status: {status}")

                if status == "completed":
                    if progress_callback:
                        elapsed_minutes = (time.time() - start_time) / 60.0
                        progress_callback(
                            100, "AssemblyAI transcription completed", elapsed_minutes
                        )
                    return result
                elif status == "error":
                    error_msg = result.get("error", "Unknown error")
                    
                    # Log detailed error information
                    logger.error(f"AssemblyAI transcription failed for transcript {transcript_id}")
                    logger.error(f"Error message: {error_msg}")
                    logger.error(f"Full error response: {result}")
                    
                    # Check if it's a URL expiration/download error
                    if ("download error" in error_msg.lower() and 
                        "unable to download" in error_msg.lower() and 
                        "x-goog-expires" in error_msg.lower()):
                        logger.warning("=" * 80)
                        logger.warning("SIGNED URL EXPIRATION DETECTED")
                        logger.warning("=" * 80)
                        logger.warning(f"The signed URL has expired and AssemblyAI cannot download the audio file.")
                        logger.warning(f"Error: {error_msg}")
                        logger.warning("This typically happens when:")
                        logger.warning("1. The transcription task is retrying after a long delay")
                        logger.warning("2. AssemblyAI queue processing took longer than expected")
                        logger.warning("3. The audio file was uploaded hours ago")
                        logger.warning("=" * 80)
                        
                        # This is a non-retryable error since the URL won't get refreshed
                        error_msg = f"Signed URL expired - audio file no longer accessible: {error_msg}"
                    
                    # Check if it's a server error that might be transient
                    elif "server error" in error_msg.lower() or "developers have been alerted" in error_msg.lower():
                        logger.warning("=" * 80)
                        logger.warning("AssemblyAI SERVICE ISSUE DETECTED")
                        logger.warning("=" * 80)
                        logger.warning(f"AssemblyAI is experiencing server issues.")
                        logger.warning(f"Error: {error_msg}")
                        logger.warning("This is likely a temporary issue on AssemblyAI's side.")
                        logger.warning("The transcription will be retried automatically.")
                        logger.warning("Consider switching to Google STT if the issue persists.")
                        logger.warning("=" * 80)
                        
                        # Mark as a temporary error that could be retried later
                        error_msg = f"AssemblyAI temporary server error: {error_msg}"
                    
                    raise STTProviderError(f"Transcription failed: {error_msg}")

                # Update progress based on elapsed time (rough estimation)
                if (
                    progress_callback
                ):  # Update progress on every poll (now every 30 seconds)
                    elapsed_minutes = (time.time() - start_time) / 60.0
                    # More conservative progress estimation with 30-second intervals
                    # Assume typical transcription takes 2-10 minutes depending on audio length
                    estimated_progress = min(90, 30 + (elapsed_minutes / 10.0) * 60)
                    progress_callback(
                        int(estimated_progress),
                        f"Processing with AssemblyAI... ({elapsed_minutes:.1f}min, {status})",
                        elapsed_minutes,
                    )

                # Still processing, wait and retry (30 seconds instead of 1 second)
                if retry_count < max_retries - 1:  # Don't sleep on the last attempt
                    logger.debug(
                        f"Waiting {polling_interval} seconds before next poll..."
                    )
                    time.sleep(polling_interval)
                retry_count += 1

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logger.error(f"Transcript not found: {transcript_id}")
                    raise STTProviderError(f"Transcript not found: {transcript_id}")
                elif e.response.status_code >= 500:
                    # Server errors - might be temporary
                    logger.warning(f"AssemblyAI server error (HTTP {e.response.status_code}): {e}")
                    logger.warning("This may be a temporary issue. Will retry...")
                    # Don't raise immediately for server errors, continue polling
                    if retry_count < max_retries - 1:
                        time.sleep(polling_interval)
                        retry_count += 1
                        continue
                    else:
                        raise STTProviderError(f"AssemblyAI server error after {max_retries} attempts: {e}")
                else:
                    logger.error(f"HTTP error polling status: {e}")
                    raise STTProviderError(f"Failed to poll status: {e}")
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error to AssemblyAI: {e}")
                if retry_count < max_retries - 1:
                    logger.info(f"Retrying after connection error... (attempt {retry_count + 1}/{max_retries})")
                    time.sleep(polling_interval)
                    retry_count += 1
                    continue
                else:
                    raise STTProviderError(f"Connection failed after {max_retries} attempts: {e}")
            except requests.exceptions.Timeout as e:
                logger.warning(f"Request timeout to AssemblyAI: {e}")
                if retry_count < max_retries - 1:
                    logger.info(f"Retrying after timeout... (attempt {retry_count + 1}/{max_retries})")
                    time.sleep(polling_interval)
                    retry_count += 1
                    continue
                else:
                    raise STTProviderError(f"Request timeout after {max_retries} attempts: {e}")
            except Exception as e:
                logger.error(f"Unexpected error polling transcription status: {e}", exc_info=True)
                raise STTProviderError(f"Failed to poll status: {e}")

        raise STTProviderError("Transcription timed out after 2 hours")

    def _parse_transcript_result(
        self,
        result: Dict[str, Any],
        original_language: str,
        enable_diarization: bool = True,
    ) -> TranscriptionResult:
        """Parse AssemblyAI transcript result into our format."""
        segments = []
        needs_conversion = self._needs_traditional_conversion(original_language)

        # Check if we have utterances (speaker diarization enabled)
        if "utterances" in result and result["utterances"]:
            for utterance in result["utterances"]:
                # Process text based on language
                text = utterance["text"]
                if result.get("language_code") == "zh" or "zh" in (
                    result.get("language_code") or ""
                ):
                    text = self._process_chinese_text(text, needs_conversion)

                segment = TranscriptSegment(
                    speaker_id=self._convert_speaker_id(utterance.get("speaker", 0)),
                    start_seconds=utterance["start"] / 1000.0,  # Convert ms to seconds
                    end_seconds=utterance["end"] / 1000.0,
                    content=text,
                    confidence=utterance.get("confidence", 1.0),
                )
                segments.append(segment)
        else:
            # No speaker diarization, use words or full text
            if "words" in result and result["words"]:
                # Group words into sentences
                current_sentence = []
                current_start = None
                current_speaker = None

                sentence_length_limit = 50  # Max words per segment

                for word in result["words"]:
                    if current_start is None:
                        current_start = word["start"]
                        current_speaker = self._convert_speaker_id(
                            word.get("speaker", 0)
                        )

                    current_sentence.append(word["text"])

                    # Check if this word ends a sentence (include more Chinese punctuation) OR segment is getting too long
                    should_break = (
                        word["text"].endswith(
                            (".", "!", "?", "。", "！", "？", "；", "：", "，")
                        )
                        or len(current_sentence) >= sentence_length_limit
                    )

                    if should_break:
                        # Create segment
                        text = " ".join(current_sentence)
                        if result.get("language_code") == "zh" or "zh" in (
                            result.get("language_code") or ""
                        ):
                            text = self._process_chinese_text(text, needs_conversion)

                        segment = TranscriptSegment(
                            speaker_id=current_speaker or 0,  # Already converted above
                            start_seconds=current_start / 1000.0,
                            end_seconds=word["end"] / 1000.0,
                            content=text,
                            confidence=word.get("confidence", 1.0),
                        )
                        segments.append(segment)

                        # Reset for next sentence
                        current_sentence = []
                        current_start = None
                        current_speaker = None

                # Handle remaining words
                if current_sentence and current_start is not None:
                    text = " ".join(current_sentence)
                    if result.get("language_code") == "zh" or "zh" in (
                        result.get("language_code") or ""
                    ):
                        text = self._process_chinese_text(text, needs_conversion)

                    segment = TranscriptSegment(
                        speaker_id=current_speaker or 0,  # Already converted above
                        start_seconds=current_start / 1000.0,
                        end_seconds=result["words"][-1]["end"] / 1000.0,
                        content=text,
                        confidence=1.0,
                    )
                    segments.append(segment)
            else:
                # Fallback to full text without timing
                text = result.get("text", "")
                if text and (
                    result.get("language_code") == "zh"
                    or "zh" in (result.get("language_code") or "")
                ):
                    text = self._process_chinese_text(text, needs_conversion)

                if text:
                    segment = TranscriptSegment(
                        speaker_id=0,
                        start_seconds=0,
                        end_seconds=result.get("audio_duration", 0),
                        content=text,
                        confidence=result.get("confidence", 1.0),
                    )
                    segments.append(segment)

        # Apply automatic speaker role assignment if diarization was enabled
        role_assignments = {}
        confidence_metrics = {}

        if enable_diarization and segments:
            unique_speakers = set(s.speaker_id for s in segments)
            speakers_detected = len(unique_speakers)

            # Check if detected speakers match expectations
            if speakers_detected < self.speakers_expected:
                logger.warning(
                    f"Speaker diarization mismatch: expected {self.speakers_expected} speakers, "
                    f"but only detected {speakers_detected} speaker(s): {sorted(unique_speakers)}. "
                    f"Audio quality or speaker separation may be insufficient."
                )
            elif speakers_detected > self.speakers_expected:
                logger.info(
                    f"Speaker diarization detected more speakers than expected: "
                    f"expected {self.speakers_expected}, detected {speakers_detected}: {sorted(unique_speakers)}"
                )

            # Attempt role assignment regardless of speaker count
            if speakers_detected >= 2:
                try:
                    role_assignments, confidence_metrics = assign_roles_simple(segments)
                    logger.info(f"Simple role assignment: {role_assignments}")
                    logger.info(
                        f"Assignment confidence: {confidence_metrics.get('confidence', 0):.2%}"
                    )
                    if confidence_metrics.get("method"):
                        logger.info(
                            f"Assignment method: {confidence_metrics['method']}"
                        )
                except Exception as e:
                    logger.warning(f"Failed to assign speaker roles automatically: {e}")
            else:
                # Single speaker detected - log this situation
                logger.warning(
                    f"Cannot assign coach/client roles: only {speakers_detected} speaker detected. "
                    f"Expected 2 speakers for coaching session. Manual role assignment may be required."
                )

        # Calculate total duration (convert from milliseconds to seconds)
        total_duration = result.get("audio_duration", 0)
        if total_duration:
            total_duration = total_duration / 1000.0  # Convert ms to seconds
        elif segments:
            total_duration = max(s.end_seconds for s in segments)

        # Prepare provider metadata
        unique_speakers = set(s.speaker_id for s in segments) if segments else set()
        speakers_detected = len(unique_speakers)

        provider_metadata = {
            "provider": "assemblyai",
            "model": self.model,
            "language_requested": original_language,
            "language_detected": result.get("language_code"),
            "post_processing_applied": (
                ["remove_spaces", "convert_to_traditional"]
                if needs_conversion
                else ["remove_spaces"]
            ),
            "transcript_id": result.get("id"),
            "confidence": result.get("confidence", 0),
            "audio_duration": result.get("audio_duration", 0),
            "speakers_expected": self.speakers_expected,
            "speakers_detected": speakers_detected,
            "speakers_detected_ids": sorted(unique_speakers),
            "speaker_diarization_mismatch": speakers_detected != self.speakers_expected,
            "speaker_role_assignments": role_assignments,
            "role_assignment_confidence": confidence_metrics,
            "automatic_role_assignment": len(role_assignments) > 0,
        }

        return TranscriptionResult(
            segments=segments,
            total_duration_sec=total_duration,
            language_code=result.get("language_code", original_language),
            cost_usd=self.estimate_cost(int(total_duration)),
            provider_metadata=provider_metadata,
        )

    def transcribe(
        self,
        audio_uri: str,
        language: str = "auto",
        enable_diarization: bool = True,
        max_speakers: int = 4,
        min_speakers: int = 2,
        progress_callback=None,
    ) -> TranscriptionResult:
        """
        Transcribe audio file with speaker diarization using AssemblyAI.

        Args:
            audio_uri: URI to audio file (HTTP/HTTPS URL or local path)
            language: Language code (cmn-Hant-TW, cmn-Hans-CN, en-US, auto)
            enable_diarization: Enable speaker separation
            max_speakers: Maximum number of speakers to detect (not used by AssemblyAI)
            min_speakers: Minimum number of speakers to detect (used as speakers_expected)

        Returns:
            TranscriptionResult with segments and metadata
        """
        try:
            # Map language code
            assemblyai_language = self._map_language_code(language)

            # Upload or get audio URL
            audio_url = self._upload_audio(audio_uri)

            # Submit transcription request
            transcript_id = self._submit_transcription(
                audio_url=audio_url,
                language_code=assemblyai_language,
                enable_diarization=enable_diarization,
                speakers_expected=min_speakers or self.speakers_expected,
            )

            # Poll for completion with progress updates
            result = self._poll_transcription_status(transcript_id, progress_callback)

            # Parse and return result
            return self._parse_transcript_result(result, language, enable_diarization)

        except (
            STTProviderError,
            STTProviderUnavailableError,
            STTProviderQuotaExceededError,
            STTProviderInvalidAudioError,
        ):
            # Re-raise provider-specific errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error in AssemblyAI transcription: {e}")
            raise STTProviderError(f"Transcription failed: {e}")

    def estimate_cost(self, duration_seconds: int) -> Decimal:
        """
        Estimate transcription cost in USD.

        Args:
            duration_seconds: Audio duration in seconds

        Returns:
            Estimated cost in USD
        """
        # AssemblyAI pricing per second
        if self.model == "best":
            cost_per_second = Decimal("0.00025")  # $0.00025/second
        else:  # nano model
            cost_per_second = Decimal("0.000125")  # $0.000125/second

        return cost_per_second * Decimal(duration_seconds)

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "assemblyai"
