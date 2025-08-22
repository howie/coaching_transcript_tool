"""
API endpoints for transcript smoothing and punctuation repair.

Provides REST endpoints to smooth AssemblyAI transcripts and repair punctuation.
"""

import logging
import time
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ..services.transcript_smoother import (
    smooth_and_punctuate,
    TranscriptProcessingError,
    MissingWordsError,
    UnsupportedLanguageError,
)
from ..services.lemur_transcript_smoother import (
    smooth_transcript_with_lemur,
    LeMURSmoothedTranscript,
    SmoothingContext
)
from .auth import get_current_user_dependency
from ..models.session import Session
from ..core.database import get_db
from sqlalchemy.orm import Session as DBSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/transcript", tags=["transcript-smoothing"])


# Request/Response Models
class TranscriptSmoothingRequest(BaseModel):
    """Request model for transcript smoothing."""
    transcript: Dict[str, Any] = Field(
        ..., 
        description="AssemblyAI transcript with utterances and words",
        example={
            "utterances": [
                {
                    "speaker": "A",
                    "start": 1000,
                    "end": 3000,
                    "confidence": 0.9,
                    "words": [
                        {"text": "你好", "start": 1000, "end": 1500, "confidence": 0.95},
                        {"text": "世界", "start": 1500, "end": 2000, "confidence": 0.92}
                    ]
                }
            ]
        }
    )
    language: str = Field(
        "auto",
        description="Language hint for processing ('auto', 'chinese', 'english', etc.)",
        example="chinese"
    )
    config: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional configuration parameters for smoothing",
        example={
            "th_short_head_sec": 0.9,
            "th_filler_max_sec": 0.6,
            "th_sent_gap_sec": 0.6
        }
    )
    custom_prompts: Optional[Dict[str, str]] = Field(
        None,
        description="Custom prompts for speaker identification and punctuation improvement",
        example={
            "speakerPrompt": "Custom speaker identification prompt...",
            "punctuationPrompt": "Custom punctuation improvement prompt..."
        }
    )


class ProcessedSegment(BaseModel):
    """A processed transcript segment."""
    speaker: str = Field(..., description="Speaker identifier")
    start_ms: int = Field(..., description="Start time in milliseconds")
    end_ms: int = Field(..., description="End time in milliseconds")
    text: str = Field(..., description="Processed text with punctuation")
    source_utterance_indices: list[int] = Field(..., description="Source utterance indices")
    note: Optional[str] = Field(None, description="Processing note")


class HeuristicStats(BaseModel):
    """Statistics for heuristic rules applied."""
    short_first_segment: int = Field(0, description="Short head backfill applications")
    filler_words: int = Field(0, description="Filler word backfill applications")
    no_terminal_punct: int = Field(0, description="No terminal punctuation cases")
    echo_backfill: int = Field(0, description="Echo/quote backfill applications")


class ProcessingStats(BaseModel):
    """Overall processing statistics."""
    moved_word_count: int = Field(..., description="Number of words moved between speakers")
    merged_segments: int = Field(..., description="Number of segments merged")
    split_segments: int = Field(..., description="Number of segments split")
    heuristic_hits: HeuristicStats = Field(..., description="Heuristic rule statistics")
    language_detected: str = Field(..., description="Detected language")
    processor_used: str = Field(..., description="Processor used for processing")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")


class TranscriptSmoothingResponse(BaseModel):
    """Response model for transcript smoothing."""
    segments: list[ProcessedSegment] = Field(..., description="Processed transcript segments")
    stats: ProcessingStats = Field(..., description="Processing statistics")
    success: bool = Field(True, description="Whether processing succeeded")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Error type")
    success: bool = Field(False, description="Processing failed")


# LeMUR-based Response Models
class LeMURSegment(BaseModel):
    """A LeMUR-processed transcript segment."""
    speaker: str = Field(..., description="Corrected speaker identifier (教練/客戶 or Coach/Client)")
    start_ms: int = Field(..., description="Start time in milliseconds")
    end_ms: int = Field(..., description="End time in milliseconds")
    text: str = Field(..., description="Text with improved punctuation and structure")


class LeMURSmoothingResponse(BaseModel):
    """Response model for LeMUR-based transcript smoothing."""
    segments: list[LeMURSegment] = Field(..., description="LeMUR-processed transcript segments")
    speaker_mapping: Dict[str, str] = Field(..., description="Original to corrected speaker mapping")
    improvements_made: list[str] = Field(..., description="List of improvements applied")
    processing_notes: str = Field(..., description="Notes about the processing")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    success: bool = Field(True, description="Whether processing succeeded")


# API Endpoints
@router.post(
    "/smooth-and-punctuate",
    response_model=TranscriptSmoothingResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input data"},
        422: {"model": ErrorResponse, "description": "Processing error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Smooth transcript and repair punctuation",
    description="""
    Process AssemblyAI transcript to smooth speaker boundaries and repair punctuation.
    
    This endpoint:
    1. Smooths speaker boundary errors (backfills short segments, filler words, etc.)
    2. Repairs Chinese/English punctuation based on language rules
    3. Maintains timing information and speaker assignments
    4. Supports multiple languages with auto-detection
    
    The processing uses configurable heuristic rules and can be customized
    for different languages and use cases.
    """
)
async def smooth_transcript(
    request: TranscriptSmoothingRequest,
    current_user=Depends(get_current_user_dependency)
) -> TranscriptSmoothingResponse:
    """
    Smooth speaker boundaries and repair punctuation in transcript.
    
    Args:
        request: Transcript smoothing request with data and configuration
        current_user: Authenticated user (required)
        
    Returns:
        Processed transcript with smoothed boundaries and repaired punctuation
        
    Raises:
        HTTPException: For various error conditions
    """
    try:
        logger.info(
            f"User {current_user.email} requested transcript smoothing for "
            f"language: {request.language}"
        )
        
        start_time = time.time()
        
        # Prepare configuration
        config_params = request.config or {}
        
        # Process transcript
        result = smooth_and_punctuate(
            transcript_json=request.transcript,
            language=request.language,
            **config_params
        )
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Convert to response format
        segments = [ProcessedSegment(**segment) for segment in result["segments"]]
        
        stats = ProcessingStats(
            **result["stats"],
            processing_time_ms=processing_time_ms
        )
        
        logger.info(
            f"Transcript smoothing completed for user {current_user.email}. "
            f"Language: {stats.language_detected}, "
            f"Segments: {len(segments)}, "
            f"Processing time: {processing_time_ms}ms"
        )
        
        return TranscriptSmoothingResponse(
            segments=segments,
            stats=stats,
            success=True
        )
        
    except MissingWordsError as e:
        logger.warning(f"Missing words error for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": str(e),
                "error_type": "missing_words",
                "success": False
            }
        )
        
    except UnsupportedLanguageError as e:
        logger.warning(f"Unsupported language error for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": str(e),
                "error_type": "unsupported_language", 
                "success": False
            }
        )
        
    except TranscriptProcessingError as e:
        logger.error(f"Transcript processing error for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=422,
            detail={
                "error": str(e),
                "error_type": "processing_error",
                "success": False
            }
        )
        
    except Exception as e:
        logger.error(f"Unexpected error during transcript smoothing for user {current_user.email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error during transcript processing",
                "error_type": "internal_error",
                "success": False
            }
        )


@router.post(
    "/lemur-smooth",
    response_model=LeMURSmoothingResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input data"},
        422: {"model": ErrorResponse, "description": "Processing error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="LeMUR-based transcript smoothing (AI-powered)",
    description="""
    Process AssemblyAI transcript using LeMUR (Large Language Model) for intelligent correction.
    
    This endpoint uses AssemblyAI's LeMUR service to:
    1. Correct speaker identification in coaching context (Coach vs Client)
    2. Add proper internal punctuation within long segments
    3. Improve text structure and readability
    4. Provide context-aware corrections that rule-based algorithms cannot achieve
    
    This is significantly more accurate than rule-based smoothing for complex tasks
    like speaker identification and punctuation repair.
    """
)
async def lemur_smooth_transcript(
    request: TranscriptSmoothingRequest,
    current_user=Depends(get_current_user_dependency)
) -> LeMURSmoothingResponse:
    """
    Smooth transcript using LeMUR AI for intelligent corrections.
    
    Args:
        request: Transcript smoothing request with AssemblyAI data
        current_user: Authenticated user (required)
        
    Returns:
        LeMUR-processed transcript with intelligent corrections
        
    Raises:
        HTTPException: For various error conditions
    """
    try:
        logger.info(
            f"User {current_user.email} requested LeMUR-based transcript smoothing for "
            f"language: {request.language}"
        )
        
        start_time = time.time()
        
        # Prepare segments for LeMUR processing
        if not request.transcript.get("utterances"):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "No utterances found in transcript. LeMUR smoothing requires speaker-segmented transcript data.",
                    "error_type": "missing_utterances",
                    "success": False
                }
            )
        
        lemur_segments = []
        for utterance in request.transcript["utterances"]:
            lemur_segments.append({
                "start": utterance["start"],  # milliseconds
                "end": utterance["end"],      # milliseconds
                "speaker": utterance.get("speaker", "A"),
                "text": utterance.get("text", "")
            })
        
        # Determine session language
        session_language = request.language
        if session_language == "auto":
            # Try to detect from transcript metadata or default to Chinese for coaching
            detected_lang = request.transcript.get("language_code", "zh-TW")
            session_language = detected_lang
        elif session_language == "chinese":
            session_language = "zh-TW"
        elif session_language == "english": 
            session_language = "en-US"
        
        logger.debug(f"Processing {len(lemur_segments)} segments with LeMUR for language: {session_language}")
        
        # Check for custom prompts
        custom_prompts = request.custom_prompts
        if custom_prompts:
            logger.info(f"Using custom prompts for LeMUR processing: {list(custom_prompts.keys())}")
        
        # Apply LeMUR-based smoothing
        smoothed_result = await smooth_transcript_with_lemur(
            segments=lemur_segments,
            session_language=session_language,
            is_coaching_session=True,
            custom_prompts=custom_prompts
        )
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Convert to response format
        response_segments = []
        for segment in smoothed_result.segments:
            response_segments.append(LeMURSegment(
                speaker=segment.speaker,
                start_ms=segment.start,
                end_ms=segment.end,
                text=segment.text
            ))
        
        logger.info(
            f"LeMUR transcript smoothing completed for user {current_user.email}. "
            f"Language: {session_language}, "
            f"Segments: {len(response_segments)}, "
            f"Processing time: {processing_time_ms}ms, "
            f"Speaker mapping: {smoothed_result.speaker_mapping}"
        )
        
        return LeMURSmoothingResponse(
            segments=response_segments,
            speaker_mapping=smoothed_result.speaker_mapping,
            improvements_made=smoothed_result.improvements_made,
            processing_notes=smoothed_result.processing_notes,
            processing_time_ms=processing_time_ms,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LeMUR transcript smoothing failed for user {current_user.email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"LeMUR processing failed: {str(e)}",
                "error_type": "lemur_error",
                "success": False
            }
        )


@router.get(
    "/smooth/config/defaults",
    response_model=Dict[str, Any],
    summary="Get default smoothing configuration",
    description="Get the default configuration parameters for transcript smoothing."
)
async def get_default_config(
    language: str = "chinese",
    current_user=Depends(get_current_user_dependency)
) -> Dict[str, Any]:
    """
    Get default configuration for transcript smoothing.
    
    Args:
        language: Language to get defaults for
        current_user: Authenticated user
        
    Returns:
        Default configuration parameters
    """
    try:
        if language.lower() == "chinese":
            from ..services.transcript_smoother import ChineseSmoothingConfig, ChineseProcessor
            
            config = ChineseSmoothingConfig()
            processor = ChineseProcessor()
            
            return {
                "language": "chinese",
                "smoothing_config": {
                    "th_short_head_sec": config.th_short_head_sec,
                    "th_filler_max_sec": config.th_filler_max_sec,
                    "th_gap_sec": config.th_gap_sec,
                    "th_max_move_sec": config.th_max_move_sec,
                    "th_echo_max_sec": config.th_echo_max_sec,
                    "th_echo_gap_sec": config.th_echo_gap_sec,
                    "echo_jaccard_tau": config.echo_jaccard_tau,
                    "n_pass": config.n_pass,
                    "filler_whitelist": config.filler_whitelist
                },
                "punctuation_config": {
                    "th_sent_gap_sec": 0.6,
                    "min_sentence_length": 3
                },
                "filler_words": processor.get_filler_words()
            }
            
        elif language.lower() == "english":
            from ..services.transcript_smoother import EnglishSmoothingConfig, EnglishProcessor
            
            config = EnglishSmoothingConfig()
            processor = EnglishProcessor()
            
            return {
                "language": "english",
                "smoothing_config": {
                    "th_short_head_sec": config.th_short_head_sec,
                    "th_filler_max_sec": config.th_filler_max_sec,
                    "th_gap_sec": config.th_gap_sec,
                    "th_max_move_sec": config.th_max_move_sec,
                    "th_echo_max_sec": config.th_echo_max_sec,
                    "th_echo_gap_sec": config.th_echo_gap_sec,
                    "echo_jaccard_tau": config.echo_jaccard_tau,
                    "n_pass": config.n_pass,
                    "filler_whitelist": config.filler_whitelist
                },
                "punctuation_config": {
                    "th_sent_gap_sec": 0.6,
                    "min_sentence_length": 3
                },
                "filler_words": processor.get_filler_words()
            }
            
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": f"Unsupported language: {language}",
                    "error_type": "unsupported_language",
                    "supported_languages": ["chinese", "english"]
                }
            )
            
    except Exception as e:
        logger.error(f"Error getting default config for language {language}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get default configuration",
                "error_type": "internal_error"
            }
        )


@router.get(
    "/smooth/languages",
    response_model=Dict[str, Any],
    summary="Get supported languages",
    description="Get list of supported languages for transcript smoothing."
)
async def get_supported_languages(
    current_user=Depends(get_current_user_dependency)
) -> Dict[str, Any]:
    """
    Get supported languages for transcript smoothing.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        List of supported languages with descriptions
    """
    return {
        "supported_languages": [
            {
                "code": "chinese",
                "name": "Chinese (Traditional/Simplified)",
                "description": "Chinese language with full-width punctuation repair",
                "auto_detected": True
            },
            {
                "code": "english", 
                "name": "English",
                "description": "English language with standard punctuation",
                "auto_detected": True
            },
            {
                "code": "auto",
                "name": "Auto-detect",
                "description": "Automatically detect language from transcript content",
                "auto_detected": False
            }
        ],
        "default_language": "auto",
        "notes": [
            "Auto-detection works best with substantial text content",
            "Chinese processing includes Traditional Chinese conversion",
            "English processing uses standard punctuation rules"
        ]
    }


@router.get(
    "/session/{session_id}/raw-data",
    response_model=Dict[str, Any],
    summary="Get raw AssemblyAI data for smoothing",
    description="Get the raw AssemblyAI transcript data for a session to use with the smoothing API."
)
async def get_raw_assemblyai_data(
    session_id: str,
    current_user=Depends(get_current_user_dependency),
    db: DBSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get raw AssemblyAI transcript data for a session.
    
    Args:
        session_id: Session ID to get raw data for
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Raw AssemblyAI transcript data if available
        
    Raises:
        HTTPException: If session not found or no raw data available
    """
    try:
        # Get the session
        session = db.query(Session).filter(
            Session.id == session_id,
            Session.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Session not found",
                    "error_type": "not_found",
                    "success": False
                }
            )
        
        # Check if this session has raw AssemblyAI data
        if (session.stt_provider != "assemblyai" or 
            not session.provider_metadata or 
            "raw_assemblyai_response" not in session.provider_metadata):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Raw AssemblyAI data not available for this session",
                    "error_type": "no_raw_data",
                    "stt_provider": session.stt_provider,
                    "success": False
                }
            )
        
        raw_data = session.provider_metadata["raw_assemblyai_response"]
        
        logger.info(
            f"Retrieved raw AssemblyAI data for session {session_id} by user {current_user.email}. "
            f"Utterances: {len(raw_data.get('utterances', []))}, "
            f"Words: {len(raw_data.get('words', []))}"
        )
        
        return {
            "session_id": session_id,
            "provider": "assemblyai",
            "raw_data": raw_data,
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting raw AssemblyAI data for session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve raw AssemblyAI data",
                "error_type": "internal_error",
                "success": False
            }
        )