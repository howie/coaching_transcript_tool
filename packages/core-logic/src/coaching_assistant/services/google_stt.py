"""Google Speech-to-Text provider implementation."""

import json
import logging
from decimal import Decimal
from typing import List, Optional, Dict, Any
from google.cloud import speech_v2
from google.cloud.speech_v2 import RecognitionConfig, RecognitionFeatures, SpeakerDiarizationConfig, ExplicitDecodingConfig
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
            # Determine regional endpoint
            default_location = settings.GOOGLE_STT_LOCATION or "us-central1"
            api_endpoint = f"{default_location}-speech.googleapis.com"
            
            # Initialize credentials - will be stored for GCS client reuse
            credentials = None
            
            # Initialize credentials from JSON string if provided
            if settings.GOOGLE_APPLICATION_CREDENTIALS_JSON:
                import tempfile
                import os
                import base64
                from google.oauth2 import service_account
                from google.api_core.client_options import ClientOptions
                
                # Handle both raw JSON and Base64 encoded JSON
                credentials_json = settings.GOOGLE_APPLICATION_CREDENTIALS_JSON
                try:
                    # First try to parse as raw JSON
                    credentials_info = json.loads(credentials_json)
                except json.JSONDecodeError:
                    # If that fails, try Base64 decoding first
                    try:
                        decoded_json = base64.b64decode(credentials_json).decode('utf-8')
                        credentials_info = json.loads(decoded_json)
                        logger.info("Successfully decoded Base64 encoded credentials")
                    except Exception as e:
                        raise STTProviderError(f"Failed to decode credentials JSON (tried both raw and Base64): {e}")
                
                credentials = service_account.Credentials.from_service_account_info(credentials_info)
                client_options = ClientOptions(api_endpoint=api_endpoint)
                self.client = speech_v2.SpeechClient(
                    credentials=credentials,
                    client_options=client_options
                )
                logger.info(f"Google STT client initialized with service account: {credentials_info.get('client_email', 'unknown')}")
                logger.info(f"Using regional endpoint: {api_endpoint}")
            else:
                # Use default credentials (for local development)
                from google.api_core.client_options import ClientOptions
                client_options = ClientOptions(api_endpoint=api_endpoint)
                self.client = speech_v2.SpeechClient(client_options=client_options)
                logger.info("Google STT client initialized with default credentials")
                logger.info(f"Using regional endpoint: {api_endpoint}")
                
            self.project_id = settings.GOOGLE_PROJECT_ID or "your-project-id"
            if not settings.GOOGLE_PROJECT_ID or self.project_id == "your-project-id":
                logger.warning("GOOGLE_PROJECT_ID is not set; using placeholder 'your-project-id'. This may break Storage client calls. Configure GOOGLE_PROJECT_ID in settings.")
            
            # Store credentials for reuse in GCS operations
            self._credentials = credentials
            
        except Exception as e:
            logger.error(f"Failed to initialize Google STT client: {e}")
            raise STTProviderError(f"Failed to initialize Google STT: {e}")
    
    def _create_storage_client(self):
        """Create GCS Storage client using same credentials as STT client."""
        from google.cloud import storage
        
        try:
            if self._credentials:
                # Use same Service Account credentials as STT client
                storage_client = storage.Client(
                    credentials=self._credentials,
                    project=self.project_id
                )
                logger.debug("GCS Storage client initialized with Service Account credentials")
            else:
                # Fallback to default credentials (for local development)
                storage_client = storage.Client(project=self.project_id)
                logger.debug("GCS Storage client initialized with default credentials")
                
            return storage_client
            
        except Exception as e:
            logger.error(f"Failed to create GCS Storage client: {e}")
            raise STTProviderError(f"Failed to create Storage client: {e}")
    
    def _wait_for_operation_with_progress(self, operation, timeout_minutes=120, progress_callback=None):
        """
        Wait for long-running operation with progress logging and reasonable timeouts.
        
        Args:
            operation: Google Cloud long-running operation
            timeout_minutes: Total timeout in minutes
            progress_callback: Optional callback function(progress_percentage, message, elapsed_time)
            
        Returns:
            Operation result
        """
        import time
        from datetime import datetime, timedelta
        
        start_time = datetime.utcnow()
        deadline = start_time + timedelta(minutes=timeout_minutes)
        last_log_time = start_time
        check_interval = 15  # Check every 15 seconds (faster polling)
        log_interval = 60    # Log progress every 1 minute (more frequent updates)
        
        logger.info(f"Started operation at {start_time.isoformat()}, timeout: {timeout_minutes} minutes")
        
        while datetime.utcnow() < deadline:
            try:
                # Try to get result with short timeout
                response = operation.result(timeout=check_interval)
                return response
                
            except Exception as e:
                error_str = str(e)
                current_time = datetime.utcnow()
                elapsed = (current_time - start_time).total_seconds()
                
                # Check if it's a timeout (expected) vs real error
                if "timeout" in error_str.lower() or "deadline" in error_str.lower():
                    # Expected timeout - operation still running
                    time_since_last_log = (current_time - last_log_time).total_seconds()
                    
                    if time_since_last_log >= log_interval:
                        remaining_minutes = (deadline - current_time).total_seconds() / 60
                        elapsed_minutes = elapsed / 60
                        
                        # Calculate estimated progress based on elapsed time
                        # This is a rough estimate since Google doesn't provide actual progress
                        progress_estimate = min(95, (elapsed_minutes / timeout_minutes) * 100)
                        
                        logger.info(f"Transcription in progress... Elapsed: {elapsed_minutes:.1f} min, Remaining: {remaining_minutes:.1f} min")
                        last_log_time = current_time
                        
                        # Call progress callback if provided
                        if progress_callback:
                            try:
                                progress_callback(
                                    progress_estimate,
                                    f"Processing audio... ({elapsed_minutes:.1f} min elapsed)",
                                    elapsed_minutes
                                )
                            except Exception as cb_error:
                                logger.warning(f"Progress callback error: {cb_error}")
                        
                        # Check operation status if available
                        try:
                            if hasattr(operation, 'done') and callable(operation.done):
                                is_done = operation.done()
                                logger.info(f"Operation status: {'Done' if is_done else 'Still processing'}")
                        except Exception:
                            pass  # Ignore status check errors
                    
                    # Continue waiting
                    time.sleep(min(check_interval, (deadline - current_time).total_seconds()))
                    continue
                else:
                    # Real error occurred
                    logger.error(f"Operation failed after {elapsed/60:.1f} minutes: {e}")
                    raise
        
        # Timeout exceeded
        elapsed_minutes = (datetime.utcnow() - start_time).total_seconds() / 60
        logger.error(f"Operation timed out after {elapsed_minutes:.1f} minutes")
        raise TimeoutError(f"Batch recognition timed out after {timeout_minutes} minutes")
    
    def _process_batch_results(self, response: Any, target_audio_uri: str) -> dict:
        """
        Process batch recognition results with detailed per-file error collection.
        
        Returns:
            dict: {
                "has_errors": bool,
                "ok_count": int, 
                "err_count": int,
                "error_details": str,
                "output_uri": str
            }
        """
        ok_count = 0
        err_count = 0
        error_messages = []
        output_uri = None
        
        if not response.results:
            return {
                "has_errors": True,
                "ok_count": 0,
                "err_count": 1,
                "error_details": "No results in batch response",
                "output_uri": None
            }
        
        # Check if target audio URI exists in results
        if target_audio_uri not in response.results:
            available_keys = list(response.results.keys())
            return {
                "has_errors": True,
                "ok_count": 0,
                "err_count": 1,
                "error_details": f"Target audio URI not found. Available: {available_keys}",
                "output_uri": None
            }
        
        file_result = response.results[target_audio_uri]
        
        # Check error status: only treat as error if code > 0
        if hasattr(file_result, 'error') and file_result.error:
            error_code = getattr(file_result.error, 'code', 0)
            error_message = getattr(file_result.error, 'message', '').strip()
            
            if error_code > 0:
                err_count += 1
                # Format error message properly, avoid empty strings
                msg_part = f": {error_message}" if error_message else " <no details>"
                error_messages.append(f"Code {error_code}{msg_part}")
                logger.error(f"File {target_audio_uri} failed with code {error_code}: {error_message or '<empty>'}")
            else:
                ok_count += 1
                logger.info(f"File {target_audio_uri} processed successfully (status code 0)")
        else:
            ok_count += 1
            logger.info(f"File {target_audio_uri} processed successfully (no error object)")
        
        # Prioritize cloud_storage_result.uri over inline URI
        if hasattr(file_result, 'cloud_storage_result') and file_result.cloud_storage_result:
            if hasattr(file_result.cloud_storage_result, 'uri') and file_result.cloud_storage_result.uri:
                output_uri = file_result.cloud_storage_result.uri
                logger.info(f"Using cloud_storage_result.uri: {output_uri}")
        
        # Fallback to file_result.uri if cloud_storage_result not available
        if not output_uri and hasattr(file_result, 'uri') and file_result.uri:
            output_uri = file_result.uri
            logger.info(f"Using file_result.uri: {output_uri}")
        
        if not output_uri:
            err_count += 1
            error_messages.append("No output URI found in result")
        
        return {
            "has_errors": err_count > 0,
            "ok_count": ok_count,
            "err_count": err_count, 
            "error_details": "; ".join(error_messages) if error_messages else "",
            "output_uri": output_uri
        }
    
    def _read_batch_results_from_gcs(self, output_uri: str) -> Any:
        """Read batch recognition results from GCS with retry logic for write visibility delays."""
        from google.cloud import storage
        import json
        import time
        from google.auth.exceptions import RefreshError
        from google.api_core.exceptions import NotFound, Forbidden

        try:
            # Parse GCS URI provided by the API response
            if not output_uri.startswith('gs://'):
                raise ValueError(f"Invalid GCS URI: {output_uri}")

            uri_parts = output_uri[5:].split('/', 1)  # Remove gs://
            bucket_name = uri_parts[0]
            blob_name = uri_parts[1] if len(uri_parts) > 1 else ""

            if not blob_name:
                raise ValueError(f"No blob name found in URI: {output_uri}")

            logger.info(f"Reading batch results from server-provided URI: {output_uri}")

            # Use retry logic with exponential backoff for GCS write visibility delays
            # Use same credentials as STT client for consistent authentication
            storage_client = self._create_storage_client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            # Retry configuration - improved based on user feedback
            max_wait_seconds = 60  # Reduced to 1 minute for faster feedback
            delay = 1.0  # Start with 1 second delay
            deadline = time.time() + max_wait_seconds
            retry_count = 0
            max_retries = 5  # Reduced retries, but with better error handling

            while time.time() < deadline and retry_count < max_retries:
                try:
                    retry_count += 1
                    logger.info(f"Attempt {retry_count}/{max_retries}: Checking if result file exists...")

                    # Check if blob exists first
                    if blob.exists():
                        logger.info(f"Result file found after {retry_count} attempts, downloading...")
                        content = blob.download_as_text()

                        # Validate the content is not empty
                        if not content or content.strip() == "":
                            logger.warning(f"Result file exists but is empty, retrying...")
                            time.sleep(delay)
                            delay = min(delay * 2, 5.0)  # Exponential backoff, max 5 seconds
                            continue

                        # Parse JSON results
                        results_data = json.loads(content)
                        logger.info(f"Successfully loaded batch recognition results from GCS after {retry_count} attempts")

                        return results_data
                    else:
                        logger.info(f"Result file not yet available, waiting {delay:.1f}s before retry {retry_count + 1}...")
                        time.sleep(delay)
                        delay = min(delay * 2, 5.0)  # Exponential backoff, max 5 seconds
                        continue

                except Forbidden as fb:
                    logger.error("GCS access denied - missing storage.objects.get on the result bucket")
                    raise STTProviderError(f"GCS permission denied: {fb}")
                except NotFound as nf:
                    logger.info(f"File not found yet, will retry ({retry_count}/{max_retries})")
                    if retry_count >= max_retries:
                        raise
                    time.sleep(delay)
                    delay = min(delay * 1.5, 3.0)
                    continue
                except RefreshError as rae:
                    # Surface a clear, actionable message about ADC/SA auth
                    hint = "Service Account recommended; or run `gcloud auth application-default login --update-adc` in the worker environment" if self._credentials is None else "Verify the bound Service Account has access and is not disabled"
                    logger.error(f"GCS auth refresh failed: {rae}. {hint}")
                    raise STTProviderError(f"GCS authentication failed (token refresh). {hint}: {rae}")
                except json.JSONDecodeError as json_err:
                    logger.warning(f"Result file exists but contains invalid JSON, retrying: {json_err}")
                    time.sleep(delay)
                    delay = min(delay * 2, 5.0)
                    continue
                except Exception as retry_err:
                    error_type = type(retry_err).__name__
                    logger.warning(f"Retry attempt {retry_count} failed ({error_type}): {retry_err}")
                    if retry_count >= max_retries:
                        raise
                    time.sleep(delay)
                    delay = min(delay * 1.5, 3.0)
                    continue

            # If we've exhausted retries or time, raise error
            raise FileNotFoundError(
                f"GCS result file not found after {retry_count} attempts and {max_wait_seconds}s wait: {output_uri}. "
                f"This may indicate the Speech-to-Text operation completed but the output file is still being written. "
                f"Please check the GCS bucket and file permissions."
            )

        except Exception as e:
            logger.error(f"Failed to read batch results from GCS URI {output_uri}: {e}")
            raise STTProviderError(f"Failed to read batch results: {e}")
    
    def _validate_diarization_support(self, language: str, model: str, enable_diarization: bool) -> bool:
        """
        Validate that the language-model combination supports diarization.
        
        Based on Google STT v2 capability matrix. Returns True if supported, False otherwise.
        """
        if not enable_diarization:
            return False
            
        # Known combinations that support diarization in Google STT v2
        # Based on Google Cloud documentation - diarization is limited to specific combinations
        diarization_supported = {
            # US region combinations that support diarization
            ("en-us", "chirp_2", "us-central1"),
            ("en-us", "latest_long", "us-central1"),
            ("en-us", "latest_short", "us-central1"),
            # Global models (limited language support)
            ("en-us", "chirp", "global"),
            ("en-gb", "chirp", "global"),
        }
        
        # Get current location from settings
        location = settings.GOOGLE_STT_LOCATION
        lang_model_location_key = (language.lower(), model.lower(), location)
        
        # Check if the combination is supported
        is_supported = lang_model_location_key in diarization_supported
        
        if not is_supported:
            logger.warning(f"Diarization not supported for {language} + {model} in {location}. "
                         f"Supported combinations: {diarization_supported}")
            return False
        
        logger.info(f"Diarization is supported for {language} + {model} in {location}")
        return True
            
    def _detect_audio_format(self, audio_uri: str, filename: str = None) -> tuple[int, int, int]:
        """
        Detect audio format from URI/filename and return encoding, sample rate, and channel count.
        
        Args:
            audio_uri: GCS URI of the audio file
            filename: Original filename (optional, extracted from URI if not provided)
        
        Returns:
            tuple: (encoding_value, sample_rate_hertz, audio_channel_count)
        """
        # Extract filename from URI if not provided
        if not filename:
            filename = audio_uri.split('/')[-1]
        
        # Get file extension
        file_extension = filename.split('.')[-1].lower()
        
        logger.info(f"Detecting audio format for: {filename} (extension: {file_extension})")
        
        # Get AudioEncoding enum from ExplicitDecodingConfig
        AudioEncoding = ExplicitDecodingConfig.AudioEncoding
        
        # Map file extensions to Google STT v2 AudioEncoding with default settings
        format_mappings = {
            # M4A format removed due to compatibility issues with Google STT batch API
            
            
            # MP4 audio (usually AAC)  
            'mp4': {
                'encoding': AudioEncoding.MP4_AAC,
                'sample_rate': 48000,
                'channels': 2
            },
            
            # MOV audio (usually AAC)  
            'mov': {
                'encoding': AudioEncoding.MOV_AAC,
                'sample_rate': 48000,
                'channels': 2
            },
            
            # MP3
            'mp3': {
                'encoding': AudioEncoding.MP3,
                'sample_rate': 44100,  # Standard CD quality
                'channels': 2
            },
            
            # FLAC
            'flac': {
                'encoding': AudioEncoding.FLAC,
                'sample_rate': 44100,
                'channels': 2
            },
            
            # WAV (usually LINEAR16)
            'wav': {
                'encoding': AudioEncoding.LINEAR16,
                'sample_rate': 44100,
                'channels': 1  # Mono is common for voice recordings
            },
            
            # WebM/OGG Opus
            'webm': {
                'encoding': AudioEncoding.WEBM_OPUS,
                'sample_rate': 48000,  # Standard for Opus
                'channels': 1
            },
            'ogg': {
                'encoding': AudioEncoding.OGG_OPUS,
                'sample_rate': 48000,
                'channels': 1
            }
        }
        
        # Get format configuration
        if file_extension in format_mappings:
            config = format_mappings[file_extension]
            encoding = config['encoding']
            sample_rate = config['sample_rate']
            channels = config['channels']
            
            logger.info(f"Audio format detected: {encoding}, {sample_rate}Hz, {channels} channel(s)")
            
            # For M4A files, add additional compatibility warning and suggest fallback
            # M4A format no longer supported - removed due to compatibility issues
            
            # For speech/coaching recordings, mono is often better
            if file_extension in ['mp4', 'mp3', 'flac'] and channels == 2:
                logger.info("Audio appears to be speech recording, using mono for better STT performance")
                channels = 1  # Force mono for speech content
            
            return encoding, sample_rate, channels
        else:
            # Fallback to LINEAR16 (most compatible format)
            logger.warning(f"Unknown audio format '{file_extension}', using LINEAR16 (WAV) defaults")
            return AudioEncoding.LINEAR16, 44100, 1
    
    def _create_explicit_decoding_config(self, audio_uri: str, filename: str = None, fallback_to_linear16: bool = False) -> ExplicitDecodingConfig:
        """Create ExplicitDecodingConfig based on detected audio format."""
        if fallback_to_linear16:
            # Use LINEAR16 as fallback for problematic files
            logger.warning("Using LINEAR16 fallback configuration")
            encoding = ExplicitDecodingConfig.AudioEncoding.LINEAR16
            sample_rate = 44100
            channels = 1
        else:
            encoding, sample_rate, channels = self._detect_audio_format(audio_uri, filename)
        
        config = ExplicitDecodingConfig(
            encoding=encoding,
            sample_rate_hertz=sample_rate,
            audio_channel_count=channels
        )
        
        logger.info(f"Created ExplicitDecodingConfig: {encoding} @ {sample_rate}Hz, {channels}ch")
        return config
    
    def _normalize_language_code(self, language: str) -> str:
        """
        Normalize language codes to BCP-47 format required by Google STT v2.
        
        Handles backward compatibility for legacy zh-TW/zh-CN codes.
        """
        language_mapping = {
            "zh-TW": "cmn-Hant-TW",  # Traditional Chinese (Taiwan)
            "zh-CN": "cmn-Hans-CN",  # Simplified Chinese (China)
            "zh-tw": "cmn-Hant-TW",  # Case insensitive
            "zh-cn": "cmn-Hans-CN",  # Case insensitive
        }
        
        # Return mapped code or original if no mapping exists
        return language_mapping.get(language, language)
    
    def transcribe(
        self,
        audio_uri: str,
        language: str = "cmn-Hant-TW",
        enable_diarization: bool = None,
        max_speakers: int = None,
        min_speakers: int = None,
        original_filename: str = None,
        progress_callback=None
    ) -> TranscriptionResult:
        """Transcribe audio using Google Speech-to-Text v2."""
        try:
            # Use settings defaults if parameters not provided
            if enable_diarization is None:
                enable_diarization = settings.ENABLE_SPEAKER_DIARIZATION
            if max_speakers is None:
                max_speakers = settings.MAX_SPEAKERS
            if min_speakers is None:
                min_speakers = settings.MIN_SPEAKERS
            
            # Normalize language code to BCP-47 format
            normalized_language = self._normalize_language_code(language)
            logger.info(f"Starting Google STT transcription for {audio_uri} (language: {language} -> {normalized_language})")
            logger.info(f"Diarization: {'enabled' if enable_diarization else 'disabled'}, Speakers: {min_speakers}-{max_speakers}")
            
            # Choose API method based on diarization requirement
            if enable_diarization:
                return self._transcribe_with_diarization(
                    audio_uri, normalized_language, max_speakers, min_speakers,
                    original_filename, progress_callback
                )
            else:
                return self._transcribe_batch_mode(
                    audio_uri, normalized_language, original_filename, progress_callback
                )
            
        except gcp_exceptions.ResourceExhausted as e:
            logger.error(f"Google STT quota exceeded: {e}")
            raise STTProviderQuotaExceededError(f"Google STT quota exceeded: {e}")
            
        except gcp_exceptions.InvalidArgument as e:
            error_msg = str(e)
            logger.error(f"Google STT InvalidArgument error: {error_msg}")
            
            # Handle specific recognizer configuration errors
            if "recognizer" in error_msg.lower() or "diarization" in error_msg.lower():
                logger.error(f"Recognizer configuration error")
                raise STTProviderError(f"STT configuration error: {error_msg}")
            else:
                raise STTProviderInvalidAudioError(f"Invalid audio file: {error_msg}")
            
        except gcp_exceptions.ServiceUnavailable as e:
            logger.error(f"Google STT service unavailable: {e}")
            raise STTProviderUnavailableError(f"Google STT service unavailable: {e}")
            
        except Exception as e:
            logger.error(f"Google STT transcription failed: {e}")
            raise STTProviderError(f"Transcription failed: {e}")
    
    def _transcribe_with_diarization(
        self,
        audio_uri: str,
        language: str,
        max_speakers: int,
        min_speakers: int,
        original_filename: str = None,
        progress_callback=None
    ) -> TranscriptionResult:
        """
        Transcribe audio using recognize API with speaker diarization support.
        This method uses the synchronous recognize API which supports diarization.
        """
        logger.info(f"Using recognize API with diarization for {audio_uri}")
        
        # Configure recognition features with diarization
        features = RecognitionFeatures(
            enable_automatic_punctuation=settings.ENABLE_PUNCTUATION,
            enable_word_time_offsets=True,
            enable_word_confidence=True,
            diarization_config=SpeakerDiarizationConfig(
                min_speaker_count=min_speakers,
                max_speaker_count=max_speakers
            )
        )
        
        # Determine the best location and model based on language
        location, model = self._get_optimal_location_and_model(language)
        
        # Validate diarization support - fallback to batch mode if not supported
        if not self._validate_diarization_support(language, model, True):
            logger.warning(f"Diarization not supported for {language}+{model} in {location}. Falling back to batch mode.")
            return self._transcribe_batch_mode(audio_uri, language, original_filename, progress_callback)
        
        # Log the configuration being used
        logger.info(f"Using location: {location}, model: {model} for language: {language}")
        logger.info(f"Diarization: enabled with {min_speakers}-{max_speakers} speakers")
        
        # Create explicit decoding config based on actual audio format
        explicit_decoding_config = self._create_explicit_decoding_config(audio_uri, original_filename)
        
        # Configure recognition with explicit decoding and diarization
        config = RecognitionConfig(
            explicit_decoding_config=explicit_decoding_config,
            language_codes=[language] if language != "auto" else ["cmn-Hant-TW", "cmn-Hans-CN", "en-US"],
            model=model,
            features=features
        )
        
        # Use ephemeral recognizer for synchronous recognition with diarization
        recognizer_path = f"projects/{self.project_id}/locations/{location}/recognizers/_"
        logger.info(f"Using ephemeral recognizer: {recognizer_path}")
        
        request = {
            "recognizer": recognizer_path,
            "config": config,
            "uri": audio_uri
        }
        
        # Execute synchronous recognition with progress updates
        logger.info("Starting synchronous recognition with diarization...")
        if progress_callback:
            progress_callback(10, "Starting recognition with speaker diarization...", 0)
        
        response = self.client.recognize(request=request)
        
        if progress_callback:
            progress_callback(90, "Processing diarization results...", 0)
        
        logger.info("Recognition completed, processing results with diarization")
        
        # Process results with diarization information
        segments = self._process_recognition_results_with_diarization(response)
        
        # Calculate duration from segments
        total_duration = max((seg.end_sec for seg in segments), default=0.0)
        
        # Estimate cost
        cost = self.estimate_cost(int(total_duration))
        
        logger.info(f"Diarized transcription completed: {len(segments)} segments, {total_duration:.1f}s duration")
        
        if progress_callback:
            progress_callback(100, "Transcription completed with speaker diarization", 0)
        
        return TranscriptionResult(
            segments=segments,
            total_duration_sec=total_duration,
            language_code=language,
            cost_usd=cost,
            provider_metadata={
                "provider": "google_stt_v2",
                "model": model,
                "location": location,
                "diarization_requested": True,
                "diarization_enabled": True,
                "method": "recognize",
                "min_speakers": min_speakers,
                "max_speakers": max_speakers
            }
        )
    
    def _transcribe_batch_mode(
        self,
        audio_uri: str,
        language: str,
        original_filename: str = None,
        progress_callback=None
    ) -> TranscriptionResult:
        """
        Transcribe audio using batchRecognize API without diarization.
        This is the original batch processing method.
        """
        logger.info(f"Using batchRecognize API without diarization for {audio_uri}")
        
        # Configure recognition features WITHOUT diarization
        features = RecognitionFeatures(
            enable_automatic_punctuation=settings.ENABLE_PUNCTUATION,
            enable_word_time_offsets=True,
            enable_word_confidence=True
        )
        
        # Determine the best location and model based on language
        location, model = self._get_optimal_location_and_model(language)
        
        # Log the configuration being used
        logger.info(f"Using location: {location}, model: {model} for language: {language}")
        logger.info(f"Diarization: disabled (using batch mode)")
        
        # Create explicit decoding config based on actual audio format
        explicit_decoding_config = self._create_explicit_decoding_config(audio_uri, original_filename)
        
        # Configure recognition with explicit decoding
        config = RecognitionConfig(
            explicit_decoding_config=explicit_decoding_config,
            language_codes=[language] if language != "auto" else ["cmn-Hant-TW", "cmn-Hans-CN", "en-US"],
            model=model,
            features=features
        )
        
        # Start long-running recognition using ephemeral recognizer
        recognizer_path = f"projects/{self.project_id}/locations/{location}/recognizers/_"
        logger.info(f"Using ephemeral recognizer: {recognizer_path}")
        
        # batchRecognize requires output configuration - results saved to GCS
        import uuid
        output_prefix = f"gs://{settings.TRANSCRIPT_STORAGE_BUCKET or settings.AUDIO_STORAGE_BUCKET}/batch-results/{uuid.uuid4()}/"
        logger.info(f"Output will be written to folder: {output_prefix}")
        
        request = {
            "recognizer": recognizer_path,
            "config": config,
            "recognition_output_config": {
                "gcs_output_config": {
                    "uri": output_prefix
                }
            },
            "files": [
                {
                    "uri": audio_uri
                }
            ]
        }
        
        # Execute recognition (this is synchronous but can take time)
        operation = self.client.batch_recognize(request=request)
        
        # Wait for operation to complete with progress tracking
        logger.info("Waiting for transcription to complete...")
        
        try:
            timeout_minutes = 120
            logger.info(f"Using {timeout_minutes} minute timeout for this file type")
            
            response = self._wait_for_operation_with_progress(
                operation, 
                timeout_minutes=timeout_minutes,
                progress_callback=progress_callback
            )
            logger.info("Batch recognition operation completed successfully")
        except (TimeoutError, Exception) as e:
            error_type = type(e).__name__
            logger.error(f"Batch recognition failed ({error_type}): {e}")
            
            # Check if operation failed with specific error
            if hasattr(operation, 'exception') and operation.exception():
                logger.error(f"Operation exception details: {operation.exception()}")
                raise STTProviderError(f"Operation failed: {operation.exception()}")
            else:
                raise STTProviderError(f"Operation error ({error_type}): {e}")
        
        # Process per-file results with detailed error collection
        results_summary = self._process_batch_results(response, audio_uri)
        
        if results_summary["has_errors"]:
            error_msg = f"STT batch operation had errors: {results_summary['error_details']}"
            logger.error(error_msg)
            raise STTProviderError(error_msg)
        
        # Use cloud_storage_result.uri as primary output location
        actual_output_uri = results_summary["output_uri"]
        logger.info(f"Using GCS result URI: {actual_output_uri}")
        logger.info(f"Batch results summary: {results_summary['ok_count']} success, {results_summary['err_count']} errors")
        
        # Read results from the actual GCS output file
        result = self._read_batch_results_from_gcs(actual_output_uri)
        
        # Process results
        segments = self._process_recognition_results(result, False)
        
        # Calculate duration from segments
        total_duration = max((seg.end_sec for seg in segments), default=0.0)
        
        # Estimate cost
        cost = self.estimate_cost(int(total_duration))
        
        logger.info(f"Batch transcription completed: {len(segments)} segments, {total_duration:.1f}s duration")
        
        return TranscriptionResult(
            segments=segments,
            total_duration_sec=total_duration,
            language_code=language,
            cost_usd=cost,
            provider_metadata={
                "provider": "google_stt_v2",
                "model": model,
                "location": location,
                "diarization_requested": False,
                "diarization_enabled": False,
                "method": "batchRecognize",
                "note": "Single speaker mode"
            }
        )
    
    def _get_optimal_location_and_model(self, language: str) -> tuple[str, str]:
        """
        Get the optimal location and model based on the language.
        
        Returns:
            tuple: (location, model)
        """
        import json
        
        # Default values from settings
        default_location = settings.GOOGLE_STT_LOCATION or "us-central1"
        default_model = settings.GOOGLE_STT_MODEL or "latest_long"
        
        # Built-in language optimizations for common languages
        # 針對說話者分離優化的模型選擇
        built_in_configs = {
            # 中文系列 - 使用 asia-southeast1 region (不支援 diarization，會自動降級到 batch mode)
            "cmn-hant-tw": {"location": default_location, "model": "chirp_2"},  # Traditional Chinese (Taiwan)
            "cmn-hans-cn": {"location": default_location, "model": "chirp_2"},  # Simplified Chinese (China)
            "zh-tw": {"location": default_location, "model": "chirp_2"},         # Legacy - Traditional Chinese
            "zh-cn": {"location": default_location, "model": "chirp_2"},         # Legacy - Simplified Chinese
            "zh": {"location": default_location, "model": "chirp_2"},            # Generic Chinese
            # 日韓語系 - 使用 asia-southeast1 region (不支援 diarization，會自動降級到 batch mode)
            "ja": {"location": default_location, "model": "chirp_2"},            # Japanese
            "ko": {"location": default_location, "model": "chirp_2"},            # Korean
            # 英語系 - 如果要啟用 diarization，建議使用 us-central1 + chirp_2/latest_long
            "en-us": {"location": default_location, "model": "chirp_2"},         # English - use chirp_2 for diarization support
            "en-gb": {"location": default_location, "model": "chirp_2"},         # British English
        }
        
        # Try to load language-specific configurations from settings
        language_configs = {}
        if settings.STT_LANGUAGE_CONFIGS:
            try:
                language_configs = json.loads(settings.STT_LANGUAGE_CONFIGS)
            except json.JSONDecodeError:
                logger.warning(f"Invalid STT_LANGUAGE_CONFIGS JSON: {settings.STT_LANGUAGE_CONFIGS}")
        
        # Check if there's a specific config for this language (user settings override built-in)
        if language.lower() in language_configs:
            config = language_configs[language.lower()]
            location = config.get("location", default_location)
            model = config.get("model", default_model)
        elif language.lower() in built_in_configs:
            # Use built-in optimized configs for common Asian languages
            config = built_in_configs[language.lower()]
            location = config.get("location", default_location)
            model = config.get("model", default_model)
        elif language.lower() == "auto":
            # For auto detection, use chirp_2 model which supports multiple languages and diarization
            location = default_location
            model = "chirp_2"
        else:
            # Use default values for unknown languages
            location = default_location
            model = default_model
        
        logger.info(f"Selected optimal config - Location: {location}, Model: {model}, Language: {language}")
        
        # Add diarization optimization suggestions
        if settings.ENABLE_SPEAKER_DIARIZATION:
            diarization_optimal_configs = {
                "en-us": {"location": "us-central1", "model": "chirp_2"},
                "en-gb": {"location": "us-central1", "model": "chirp_2"},
            }
            
            if language.lower() in diarization_optimal_configs:
                optimal = diarization_optimal_configs[language.lower()]
                if location != optimal["location"] or model != optimal["model"]:
                    logger.info(f"💡 For optimal diarization with {language}, consider using: "
                              f"location={optimal['location']}, model={optimal['model']}")
        
        return location, model
    
    def _process_recognition_results(
        self, 
        result: Any, 
        enable_diarization: bool
    ) -> List[TranscriptSegment]:
        """Process Google STT batch results into transcript segments."""
        segments = []
        
        # Handle different possible result formats from batch API
        results_list = []
        
        if hasattr(result, 'results'):
            # If result is an operation response object
            for batch_result in result.results:
                if hasattr(batch_result, 'results'):
                    results_list.extend(batch_result.results)
        elif isinstance(result, dict):
            # If result is parsed JSON from GCS
            if 'results' in result:
                results_list = result['results']
        elif isinstance(result, list):
            # If result is directly a list of results
            results_list = result
        
        logger.info(f"Processing {len(results_list)} recognition results")
        
        for recognition_result in results_list:
            # Handle both object attributes and dict keys
            alternatives = []
            if hasattr(recognition_result, 'alternatives'):
                alternatives = recognition_result.alternatives
            elif isinstance(recognition_result, dict) and 'alternatives' in recognition_result:
                alternatives = recognition_result['alternatives']
            
            for alternative in alternatives:
                    # batchRecognize doesn't support diarization, so process as single speaker
                    # TODO: Implement post-processing speaker diarization if needed
                    
                    # Extract words and transcript - handle both objects and dicts
                    words = []
                    transcript = ""
                    confidence = 0.8
                    
                    if hasattr(alternative, 'words'):
                        words = alternative.words
                        transcript = alternative.transcript
                        confidence = getattr(alternative, 'confidence', 0.8)
                    elif isinstance(alternative, dict):
                        words = alternative.get('words', [])
                        transcript = alternative.get('transcript', '')
                        confidence = alternative.get('confidence', 0.8)
                    
                    if words:
                        # Use word-level timing information to create more accurate segments
                        first_word = words[0]
                        last_word = words[-1]
                        
                        # Debug logging to understand the data structure
                        logger.debug(f"Processing {len(words)} words, first word type: {type(first_word)}")
                        if isinstance(first_word, dict):
                            logger.debug(f"First word dict keys: {first_word.keys()}")

                        # Handle both object attributes and dict keys for timing
                        if hasattr(first_word, 'start_time'):
                            start_time = first_word.start_time
                            end_time = last_word.end_time
                            start_sec = start_time.seconds + getattr(start_time, 'nanos', 0) / 1e9
                            end_sec = end_time.seconds + getattr(end_time, 'nanos', 0) / 1e9
                            logger.debug(f"Using object timing: {start_sec:.2f}s - {end_sec:.2f}s")
                        elif isinstance(first_word, dict):
                            start_time = first_word.get('startTime', '0s')
                            end_time = last_word.get('endTime', '5s')
                            # Parse duration strings like "1.23s"
                            start_sec = float(start_time.rstrip('s')) if start_time.endswith('s') else 0.0
                            end_sec = float(end_time.rstrip('s')) if end_time.endswith('s') else 5.0
                            logger.debug(f"Using dict timing: {start_sec:.2f}s - {end_sec:.2f}s (from {start_time} - {end_time})")
                        else:
                            start_sec = 0.0
                            end_sec = 5.0
                            logger.warning(f"Unknown word format, using default timing")

                        # Calculate average confidence from words
                        word_confidences = []
                        for word in words:
                            if hasattr(word, 'confidence'):
                                word_confidences.append(word.confidence)
                            elif isinstance(word, dict) and 'confidence' in word:
                                word_confidences.append(word['confidence'])
                        avg_confidence = sum(word_confidences) / len(word_confidences) if word_confidences else confidence

                        segments.append(TranscriptSegment(
                            speaker_id=1,  # Single speaker since no diarization
                            start_sec=start_sec,
                            end_sec=end_sec,
                            content=transcript.strip(),
                            confidence=avg_confidence
                        ))
                    else:
                        # Fallback for alternatives without word-level data
                        # Use segment index to estimate timing based on average speaking rate
                        # Average speaking rate is ~150 words per minute or ~2.5 words per second
                        words_in_segment = len(transcript.split())
                        estimated_duration = max(1.0, words_in_segment / 2.5)  # At least 1 second per segment
                        
                        # Use accumulated time from previous segments
                        if segments:
                            last_segment = segments[-1]
                            start_sec = last_segment.end_sec + 0.5  # Add 0.5 second gap between segments
                        else:
                            start_sec = 0.0
                        
                        end_sec = start_sec + estimated_duration
                        
                        logger.warning(f"No word-level timing data available, using estimated timing: {start_sec:.1f}s - {end_sec:.1f}s for {words_in_segment} words")
                        
                        segments.append(TranscriptSegment(
                            speaker_id=1,
                            start_sec=start_sec,
                            end_sec=end_sec,
                            content=transcript.strip(),
                            confidence=confidence
                        ))
        
        return segments
    
    def _process_recognition_results_with_diarization(self, response: Any) -> List[TranscriptSegment]:
        """Process Google STT recognize results with speaker diarization."""
        segments = []
        
        if not response.results:
            logger.warning("No results in recognition response")
            return segments
        
        logger.info(f"Processing {len(response.results)} recognition results with diarization")
        
        for recognition_result in response.results:
            alternatives = recognition_result.alternatives
            
            for alternative in alternatives:
                # With diarization, the words will have speaker_tag information
                if hasattr(alternative, 'words') and alternative.words:
                    words = alternative.words
                    
                    # Group words by speaker
                    speaker_groups = {}
                    for word in words:
                        speaker_tag = getattr(word, 'speaker_tag', 1)  # Default to speaker 1 if no tag
                        
                        if speaker_tag not in speaker_groups:
                            speaker_groups[speaker_tag] = []
                        speaker_groups[speaker_tag].append(word)
                    
                    logger.info(f"Found {len(speaker_groups)} speakers in this segment")
                    
                    # Create segments for each speaker group
                    for speaker_tag, speaker_words in speaker_groups.items():
                        if not speaker_words:
                            continue
                            
                        # Group consecutive words from same speaker into segments
                        current_segment_words = []
                        
                        for word in speaker_words:
                            if not current_segment_words:
                                current_segment_words.append(word)
                            else:
                                # Check if this word is consecutive (within 2 seconds of the last word)
                                last_word = current_segment_words[-1]
                                last_end = last_word.end_time.seconds + last_word.end_time.nanos / 1e9
                                current_start = word.start_time.seconds + word.start_time.nanos / 1e9
                                
                                if current_start - last_end <= 2.0:
                                    current_segment_words.append(word)
                                else:
                                    # Create segment from accumulated words
                                    if current_segment_words:
                                        segment = self._create_segment_from_words(current_segment_words, speaker_tag)
                                        segments.append(segment)
                                    
                                    # Start new segment
                                    current_segment_words = [word]
                        
                        # Process remaining words in the last segment
                        if current_segment_words:
                            segment = self._create_segment_from_words(current_segment_words, speaker_tag)
                            segments.append(segment)
                            
                else:
                    # Fallback for alternatives without word-level data
                    logger.warning("No word-level timing data in diarization result, using fallback")
                    confidence = getattr(alternative, 'confidence', 0.8)
                    transcript = alternative.transcript
                    
                    # Create a single segment (no speaker separation)
                    segments.append(TranscriptSegment(
                        speaker_id=1,
                        start_sec=0.0,
                        end_sec=len(transcript.split()) / 2.5,  # Rough estimate
                        content=transcript.strip(),
                        confidence=confidence
                    ))
        
        # Sort segments by start time
        segments.sort(key=lambda s: s.start_sec)
        
        logger.info(f"Created {len(segments)} diarized segments")
        return segments
    
    def _create_segment_from_words(self, words: List[Any], speaker_id: int) -> TranscriptSegment:
        """Create a transcript segment from a list of words."""
        if not words:
            raise ValueError("Cannot create segment from empty word list")

        # Extract timing and content
        start_time = words[0].start_time
        end_time = words[-1].end_time

        start_sec = start_time.seconds + getattr(start_time, 'nanos', 0) / 1e9
        end_sec = end_time.seconds + getattr(end_time, 'nanos', 0) / 1e9

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