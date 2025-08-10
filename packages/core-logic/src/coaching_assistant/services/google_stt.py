"""Google Speech-to-Text provider implementation."""

import asyncio
import json
import logging
from decimal import Decimal
from typing import List, Optional, Dict, Any
from google.cloud import speech_v2
from google.cloud.speech_v2 import RecognitionConfig, SpeakerDiarizationConfig
from google.api_core import exceptions as gcp_exceptions

from .stt_provider import (
    STTProvider, 
    TranscriptSegment, 
    TranscriptionResult,
    STTProviderError,
    STTProviderUnavailableError, 
    STTProviderQuotaExceededError,
    STTProviderInvalidAudioError
)
from ..core.config import settings

logger = logging.getLogger(__name__)


class GoogleSTTProvider(STTProvider):
    """Google Speech-to-Text v2 provider implementation."""
    
    def __init__(self):
        """Initialize Google STT client."""
        try:
            # Initialize credentials from JSON string if provided
            if settings.GOOGLE_APPLICATION_CREDENTIALS_JSON:
                import tempfile
                import os
                from google.oauth2 import service_account
                
                # Create temporary credentials file
                credentials_info = json.loads(settings.GOOGLE_APPLICATION_CREDENTIALS_JSON)
                credentials = service_account.Credentials.from_service_account_info(credentials_info)
                self.client = speech_v2.SpeechClient(credentials=credentials)
            else:
                # Use default credentials (for local development)
                self.client = speech_v2.SpeechClient()
                
            self.project_id = settings.GOOGLE_PROJECT_ID or "your-project-id"
            
        except Exception as e:
            logger.error(f"Failed to initialize Google STT client: {e}")
            raise STTProviderError(f"Failed to initialize Google STT: {e}")
    
    def transcribe(
        self,
        audio_uri: str,
        language: str = "zh-TW",
        enable_diarization: bool = True,
        max_speakers: int = 4,
        min_speakers: int = 2
    ) -> TranscriptionResult:
        """Transcribe audio using Google Speech-to-Text v2."""
        try:
            logger.info(f"Starting Google STT transcription for {audio_uri}")
            
            # Configure recognition
            config = RecognitionConfig(
                auto_decoding_config={},  # Auto-detect audio format
                language_codes=[language] if language != "auto" else ["zh-TW", "zh-CN", "en-US"],
                model="long",  # Use long model for better accuracy
                features={
                    "enable_automatic_punctuation": True,
                    "enable_word_time_offsets": True,
                    "enable_word_confidence": True,
                }
            )
            
            # Configure speaker diarization if enabled
            if enable_diarization:
                config.features["diarization_config"] = SpeakerDiarizationConfig(
                    enable_speaker_diarization=True,
                    min_speaker_count=min_speakers,
                    max_speaker_count=max_speakers
                )
            
            # Start long-running recognition
            request = {
                "recognizer": f"projects/{self.project_id}/locations/global/recognizers/_",
                "config": config,
                "uri": audio_uri
            }
            
            # Execute recognition (this is synchronous but can take time)
            operation = self.client.batch_recognize(request=request)
            
            # Wait for operation to complete
            logger.info("Waiting for transcription to complete...")
            result = operation.result(timeout=7200)  # 2 hours timeout
            
            # Process results
            segments = self._process_recognition_results(result, enable_diarization)
            
            # Calculate duration from segments
            total_duration = max((seg.end_sec for seg in segments), default=0.0)
            
            # Estimate cost
            cost = self.estimate_cost(int(total_duration))
            
            logger.info(f"Transcription completed: {len(segments)} segments, {total_duration:.1f}s duration")
            
            return TranscriptionResult(
                segments=segments,
                total_duration_sec=total_duration,
                language_code=language,
                cost_usd=cost,
                provider_metadata={
                    "provider": "google_stt_v2",
                    "model": "long",
                    "diarization_enabled": enable_diarization
                }
            )
            
        except gcp_exceptions.ResourceExhausted as e:
            logger.error(f"Google STT quota exceeded: {e}")
            raise STTProviderQuotaExceededError(f"Google STT quota exceeded: {e}")
            
        except gcp_exceptions.InvalidArgument as e:
            logger.error(f"Invalid audio file: {e}")
            raise STTProviderInvalidAudioError(f"Invalid audio file: {e}")
            
        except gcp_exceptions.ServiceUnavailable as e:
            logger.error(f"Google STT service unavailable: {e}")
            raise STTProviderUnavailableError(f"Google STT service unavailable: {e}")
            
        except Exception as e:
            logger.error(f"Google STT transcription failed: {e}")
            raise STTProviderError(f"Transcription failed: {e}")
    
    def _process_recognition_results(
        self, 
        result: Any, 
        enable_diarization: bool
    ) -> List[TranscriptSegment]:
        """Process Google STT results into transcript segments."""
        segments = []
        
        for batch_result in result.results:
            for recognition_result in batch_result.results:
                for alternative in recognition_result.alternatives:
                    if enable_diarization and hasattr(alternative, 'words'):
                        # Group words by speaker
                        current_speaker = None
                        current_words = []
                        
                        for word_info in alternative.words:
                            speaker_tag = getattr(word_info, 'speaker_tag', 1)
                            
                            if current_speaker != speaker_tag:
                                # Save previous segment
                                if current_words:
                                    segments.append(self._create_segment_from_words(
                                        current_words, current_speaker
                                    ))
                                
                                # Start new segment
                                current_speaker = speaker_tag
                                current_words = [word_info]
                            else:
                                current_words.append(word_info)
                        
                        # Don't forget the last segment
                        if current_words:
                            segments.append(self._create_segment_from_words(
                                current_words, current_speaker
                            ))
                    
                    else:
                        # No diarization - create single segment
                        start_time = getattr(recognition_result, 'result_end_time', None)
                        if start_time:
                            start_sec = start_time.seconds + start_time.microseconds / 1e6
                            end_sec = start_sec + 5.0  # Estimate 5 second segments
                        else:
                            start_sec = 0.0
                            end_sec = 5.0
                            
                        segments.append(TranscriptSegment(
                            speaker_id=1,
                            start_sec=start_sec,
                            end_sec=end_sec,
                            content=alternative.transcript.strip(),
                            confidence=alternative.confidence
                        ))
        
        return segments
    
    def _create_segment_from_words(self, words: List[Any], speaker_id: int) -> TranscriptSegment:
        """Create a transcript segment from a list of words."""
        if not words:
            raise ValueError("Cannot create segment from empty word list")
        
        # Extract timing and content
        start_time = words[0].start_time
        end_time = words[-1].end_time
        
        start_sec = start_time.seconds + start_time.microseconds / 1e6
        end_sec = end_time.seconds + end_time.microseconds / 1e6
        
        # Combine word text
        content = " ".join(word.word for word in words)
        
        # Average confidence
        confidences = [getattr(word, 'confidence', 1.0) for word in words]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.8
        
        return TranscriptSegment(
            speaker_id=speaker_id,
            start_sec=start_sec,
            end_sec=end_sec,
            content=content.strip(),
            confidence=avg_confidence
        )
    
    def estimate_cost(self, duration_seconds: int) -> Decimal:
        """
        Estimate Google STT cost.
        
        Google Speech-to-Text pricing (as of 2024):
        - Standard model: $0.016 per minute
        - Enhanced/Long model: $0.048 per minute
        """
        duration_minutes = duration_seconds / 60.0
        cost_per_minute = Decimal("0.048")  # Long model pricing
        return Decimal(str(duration_minutes)) * cost_per_minute
    
    @property
    def provider_name(self) -> str:
        return "google_stt_v2"