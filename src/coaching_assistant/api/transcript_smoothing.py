"""
API endpoints for transcript smoothing and punctuation repair.

Provides REST endpoints to smooth AssemblyAI transcripts and repair punctuation.
"""

import logging
import time
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional

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
from ..models.transcript import TranscriptSegment as TranscriptSegmentModel
from ..models.coaching_session import CoachingSession
from ..core.database import get_db
from sqlalchemy.orm import Session as DBSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/transcript", tags=["transcript-smoothing"])


def resolve_transcript_session_id(session_id: str, user_id: str, db: DBSession) -> tuple[str, bool]:
    """
    Resolve session ID to actual transcript session ID.
    
    IMPORTANT: There are two types of session IDs in this system:
    1. Coaching Session ID - Used in URLs like /dashboard/sessions/{id}
    2. Transcript Session ID - Contains actual transcript segments
    
    Args:
        session_id: Input session ID (could be coaching or transcript session)
        user_id: Current user ID for access control
        db: Database session
        
    Returns:
        Tuple of (transcript_session_id, is_coaching_session)
        
    Raises:
        HTTPException: If no valid session found
    """
    # First try to find as coaching session
    coaching_session = db.query(CoachingSession).filter(
        CoachingSession.id == session_id,
        CoachingSession.user_id == user_id
    ).first()
    
    if coaching_session and coaching_session.transcription_session_id:
        logger.info(f"✅ Resolved coaching session {session_id} -> transcript session {coaching_session.transcription_session_id}")
        return str(coaching_session.transcription_session_id), True
    
    # Try as direct transcript session
    transcript_session = db.query(Session).filter(
        Session.id == session_id,
        Session.user_id == user_id
    ).first()
    
    if transcript_session:
        logger.info(f"✅ Using direct transcript session {session_id}")
        return session_id, False
    
    # Neither found
    logger.warning(f"❌ No session found for ID {session_id} and user {user_id}")
    raise HTTPException(
        status_code=404,
        detail={
            "error": "Session not found or access denied. Please check if the session ID is correct.",
            "error_type": "session_not_found",
            "success": False,
            "session_id": session_id
        }
    )


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


class DBProcessingRequest(BaseModel):
    """Request model for database-based processing."""
    custom_prompts: Optional[Dict[str, str]] = Field(None, description="Optional custom prompts")


class CombinedProcessingRequest(TranscriptSmoothingRequest):
    """Request model for combined LeMUR processing."""
    use_combined_mode: bool = Field(
        True, 
        description="Force enable combined processing mode (overrides configuration)"
    )


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

@router.post(
    "/lemur-speaker-identification",
    response_model=LeMURSmoothingResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input data"},
        422: {"model": ErrorResponse, "description": "Processing error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="LeMUR-based speaker identification only",
    description="""
    Process AssemblyAI transcript using LeMUR for speaker identification only.
    
    This endpoint uses AssemblyAI's LeMUR service to:
    1. Correct speaker identification in coaching context (Coach vs Client)
    2. Keep original text and punctuation unchanged
    
    Useful when you only want to fix speaker assignments without modifying the transcript content.
    """
)

@router.post(
    "/lemur-punctuation-optimization", 
    response_model=LeMURSmoothingResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input data"},
        422: {"model": ErrorResponse, "description": "Processing error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="LeMUR-based punctuation optimization only",
    description="""
    Process AssemblyAI transcript using LeMUR for punctuation optimization only.
    
    This endpoint uses AssemblyAI's LeMUR service to:
    1. Add proper internal punctuation within long segments
    2. Improve text structure and readability
    3. Keep original speaker assignments unchanged
    
    Useful when you only want to improve punctuation without changing speaker identification.
    """
)
async def lemur_punctuation_optimization(
    request: TranscriptSmoothingRequest,
    current_user=Depends(get_current_user_dependency)
) -> LeMURSmoothingResponse:
    """Process transcript using LeMUR for punctuation optimization only."""
    # Implementation will be the same as speaker identification but with punctuation_optimization_only=True
    # This is handled by the existing logic in the service
    pass


@router.post(
    "/lemur-combined-processing",
    response_model=LeMURSmoothingResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input data"},
        422: {"model": ErrorResponse, "description": "Processing error"}, 
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Combined LeMUR processing (Speaker + Punctuation)",
    description="""
    Process AssemblyAI transcript using LeMUR for combined speaker identification and punctuation optimization.
    
    This endpoint uses AssemblyAI's LeMUR service with Claude 4 Sonnet to:
    1. Identify speakers (Coach vs Client) in coaching context
    2. Optimize punctuation and text structure
    3. Perform both tasks in a single LeMUR call for improved consistency and efficiency
    4. Reduce API calls by 50% compared to sequential processing
    
    Benefits of combined processing:
    - Higher accuracy through contextual understanding
    - Better consistency between speaker roles and text improvements
    - Faster processing with fewer API calls
    - Advanced reasoning with Claude 4 Sonnet model
    """
)
async def lemur_combined_processing(
    request: CombinedProcessingRequest,
    current_user=Depends(get_current_user_dependency)
) -> LeMURSmoothingResponse:
    """
    Process transcript using LeMUR for combined speaker identification and punctuation optimization.
    
    Args:
        request: Combined processing request with transcript data and options
        current_user: Authenticated user (required)
        
    Returns:
        LeMUR-processed transcript with both speaker corrections and punctuation improvements
        
    Raises:
        HTTPException: For various error conditions
    """
    try:
        logger.info(
            f"User {current_user.email} requested LeMUR-based combined processing for "
            f"language: {request.language}"
        )
        
        start_time = time.time()
        
        # Prepare segments for LeMUR processing
        if not request.transcript.get("utterances"):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "No utterances found in transcript. LeMUR processing requires speaker-segmented transcript data.",
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
            detected_lang = request.transcript.get("language_code", "zh-TW")
            session_language = detected_lang
        elif session_language == "chinese":
            session_language = "zh-TW"
        elif session_language == "english": 
            session_language = "en-US"
        
        logger.debug(f"Processing {len(lemur_segments)} segments for combined processing with language: {session_language}")
        
        # Apply LeMUR-based combined processing
        smoothed_result = await smooth_transcript_with_lemur(
            segments=lemur_segments,
            session_language=session_language,
            is_coaching_session=True,
            custom_prompts=request.custom_prompts,
            use_combined_processing=request.use_combined_mode
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
            f"LeMUR combined processing completed for user {current_user.email}. "
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
        logger.error(f"LeMUR combined processing failed for user {current_user.email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"LeMUR combined processing failed: {str(e)}",
                "error_type": "lemur_error",
                "success": False
            }
        )


async def lemur_speaker_identification(
    request: TranscriptSmoothingRequest,
    current_user=Depends(get_current_user_dependency)
) -> LeMURSmoothingResponse:
    """
    Process transcript using LeMUR for speaker identification only.
    
    Args:
        request: Transcript smoothing request with AssemblyAI data
        current_user: Authenticated user (required)
        
    Returns:
        LeMUR-processed transcript with corrected speaker identification
        
    Raises:
        HTTPException: For various error conditions
    """
    try:
        logger.info(
            f"User {current_user.email} requested LeMUR-based speaker identification for "
            f"language: {request.language}"
        )
        
        start_time = time.time()
        
        # Prepare segments for LeMUR processing
        if not request.transcript.get("utterances"):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "No utterances found in transcript. LeMUR processing requires speaker-segmented transcript data.",
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
            detected_lang = request.transcript.get("language_code", "zh-TW")
            session_language = detected_lang
        elif session_language == "chinese":
            session_language = "zh-TW"
        elif session_language == "english": 
            session_language = "en-US"
        
        logger.debug(f"Processing {len(lemur_segments)} segments for speaker identification with language: {session_language}")
        
        # Apply LeMUR-based speaker identification only
        smoothed_result = await smooth_transcript_with_lemur(
            segments=lemur_segments,
            session_language=session_language,
            is_coaching_session=True,
            custom_prompts=request.custom_prompts,
            speaker_identification_only=True  # New parameter for speaker-only processing
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
            f"LeMUR speaker identification completed for user {current_user.email}. "
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
        logger.error(f"LeMUR speaker identification failed for user {current_user.email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"LeMUR speaker identification failed: {str(e)}",
                "error_type": "lemur_error",
                "success": False
            }
        )


async def lemur_punctuation_optimization(
    request: TranscriptSmoothingRequest,
    current_user=Depends(get_current_user_dependency)
) -> LeMURSmoothingResponse:
    """
    Process transcript using LeMUR for punctuation optimization only.
    
    Args:
        request: Transcript smoothing request with AssemblyAI data
        current_user: Authenticated user (required)
        
    Returns:
        LeMUR-processed transcript with improved punctuation
        
    Raises:
        HTTPException: For various error conditions
    """
    try:
        logger.info(
            f"User {current_user.email} requested LeMUR-based punctuation optimization for "
            f"language: {request.language}"
        )
        
        start_time = time.time()
        
        # Prepare segments for LeMUR processing
        if not request.transcript.get("utterances"):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "No utterances found in transcript. LeMUR processing requires speaker-segmented transcript data.",
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
            detected_lang = request.transcript.get("language_code", "zh-TW")
            session_language = detected_lang
        elif session_language == "chinese":
            session_language = "zh-TW"
        elif session_language == "english": 
            session_language = "en-US"
        
        logger.debug(f"Processing {len(lemur_segments)} segments for punctuation optimization with language: {session_language}")
        
        # Apply LeMUR-based punctuation optimization only
        smoothed_result = await smooth_transcript_with_lemur(
            segments=lemur_segments,
            session_language=session_language,
            is_coaching_session=True,
            custom_prompts=request.custom_prompts,
            punctuation_optimization_only=True  # New parameter for punctuation-only processing
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
            f"LeMUR punctuation optimization completed for user {current_user.email}. "
            f"Language: {session_language}, "
            f"Segments: {len(response_segments)}, "
            f"Processing time: {processing_time_ms}ms"
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
        logger.error(f"LeMUR punctuation optimization failed for user {current_user.email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"LeMUR punctuation optimization failed: {str(e)}",
                "error_type": "lemur_error",
                "success": False
            }
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


@router.post(
    "/session/{session_id}/lemur-speaker-identification",
    response_model=LeMURSmoothingResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input data"},
        404: {"model": ErrorResponse, "description": "Session not found"},
        422: {"model": ErrorResponse, "description": "Processing error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="LeMUR speaker identification from database segments",
    description="""
    Process existing database segments using LeMUR for speaker identification only.
    
    This endpoint:
    1. Loads segments directly from the database for the given session
    2. Uses LeMUR to correct speaker identification
    3. Keeps original text content unchanged
    4. Updates the database with corrected speaker assignments
    """
)
async def lemur_speaker_identification_from_db(
    session_id: str,
    request: DBProcessingRequest,
    current_user=Depends(get_current_user_dependency),
    db: DBSession = Depends(get_db)
) -> LeMURSmoothingResponse:
    """
    Apply LeMUR speaker identification to existing database segments.
    
    Args:
        session_id: Session ID to process
        request: Request with custom_prompts
        current_user: Authenticated user
        db: Database session
        
    Returns:
        LeMUR-processed segments with corrected speakers
    """
    try:
        logger.info(f"User {current_user.email} requested DB-based speaker identification for session {session_id}")
        
        # Extract custom prompts from request
        custom_prompts = request.custom_prompts or {}
        
        # Resolve session ID (coaching -> transcript mapping)
        transcript_session_id, is_coaching = resolve_transcript_session_id(
            session_id, current_user.id, db
        )
        
        # Load segments from database using the transcript session ID
        db_segments = db.query(TranscriptSegmentModel).filter(
            TranscriptSegmentModel.session_id == transcript_session_id
        ).order_by(TranscriptSegmentModel.start_seconds).all()
        
        if not db_segments:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "No transcript segments found for this session",
                    "error_type": "no_segments",
                    "success": False
                }
            )
        
        # Fetch the session to get language information
        session = db.query(Session).filter(
            Session.id == transcript_session_id,
            Session.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Session not found",
                    "error_type": "session_not_found",
                    "success": False
                }
            )
        
        # Convert database segments to LeMUR format
        lemur_segments = []
        for segment in db_segments:
            # Map speaker_id to speaker label
            speaker_label = f"Speaker_{segment.speaker_id}" if segment.speaker_id else "A"
            
            lemur_segments.append({
                "start": int(segment.start_seconds * 1000),  # Convert to milliseconds
                "end": int(segment.end_seconds * 1000),      # Convert to milliseconds
                "speaker": speaker_label,
                "text": segment.content
            })
        
        logger.info(f"Loaded {len(lemur_segments)} segments from database for speaker identification")
        
        # Determine session language
        session_language = session.language or "zh-TW"
        if session_language.startswith("zh"):
            session_language = "zh-TW"
        elif session_language.startswith("en"):
            session_language = "en-US"
        
        start_time = time.time()
        
        # Apply LeMUR-based speaker identification only
        smoothed_result = await smooth_transcript_with_lemur(
            segments=lemur_segments,
            session_language=session_language,
            is_coaching_session=True,
            custom_prompts=custom_prompts,
            speaker_identification_only=True
        )
        
        # Update database segments with corrected speakers
        segment_updates = 0
        speaker_comparisons_logged = 0
        for i, corrected_segment in enumerate(smoothed_result.segments):
            if i < len(db_segments):
                db_segment = db_segments[i]
                
                # Map corrected speaker back to speaker_id
                if corrected_segment.speaker in ['教練', 'Coach']:
                    new_speaker_id = 1
                elif corrected_segment.speaker in ['客戶', 'Client']:
                    new_speaker_id = 2
                else:
                    # Keep original speaker_id if no clear mapping
                    new_speaker_id = db_segment.speaker_id
                
                # Debug: Log first few speaker comparisons to show what LeMUR changed
                if speaker_comparisons_logged < 3:
                    logger.info(f"🎭 SPEAKER COMPARISON {i+1}:")
                    logger.info(f"   Original: speaker_id={db_segment.speaker_id}")
                    logger.info(f"   Corrected: speaker='{corrected_segment.speaker}' → speaker_id={new_speaker_id}")
                    logger.info(f"   Changed: {db_segment.speaker_id != new_speaker_id}")
                    speaker_comparisons_logged += 1
                
                if db_segment.speaker_id != new_speaker_id:
                    db_segment.speaker_id = new_speaker_id
                    segment_updates += 1
        
        # Commit changes to database
        if segment_updates > 0:
            db.commit()
            logger.info(f"Updated {segment_updates} segments with corrected speaker assignments")
        else:
            logger.info("No speaker assignments needed updating")
        
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
        
        logger.info(f"DB-based speaker identification completed: {len(response_segments)} segments, {segment_updates} updates")
        
        return LeMURSmoothingResponse(
            segments=response_segments,
            speaker_mapping=smoothed_result.speaker_mapping,
            improvements_made=smoothed_result.improvements_made + [f"Updated {segment_updates} speaker assignments in database"],
            processing_notes=f"DB-based processing: {smoothed_result.processing_notes}",
            processing_time_ms=processing_time_ms,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DB-based speaker identification failed for session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Speaker identification failed: {str(e)}",
                "error_type": "processing_error",
                "success": False
            }
        )


@router.post(
    "/session/{session_id}/lemur-punctuation-optimization",
    response_model=LeMURSmoothingResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input data"},
        404: {"model": ErrorResponse, "description": "Session not found"},
        422: {"model": ErrorResponse, "description": "Processing error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="LeMUR punctuation optimization from database segments",
    description="""
    Process existing database segments using LeMUR for punctuation optimization only.
    
    This endpoint:
    1. Loads segments directly from the database for the given session
    2. Uses LeMUR to improve punctuation and text structure
    3. Keeps original speaker assignments unchanged
    4. Updates the database with improved text content
    """
)
async def lemur_punctuation_optimization_from_db(
    session_id: str,
    request: DBProcessingRequest,
    current_user=Depends(get_current_user_dependency),
    db: DBSession = Depends(get_db)
) -> LeMURSmoothingResponse:
    """
    Apply LeMUR punctuation optimization to existing database segments.
    
    Args:
        session_id: Session ID to process
        request: Request with custom_prompts
        current_user: Authenticated user
        db: Database session
        
    Returns:
        LeMUR-processed segments with improved punctuation
    """
    try:
        logger.info(f"User {current_user.email} requested DB-based punctuation optimization for session {session_id}")
        
        # Extract custom prompts from request
        custom_prompts = request.custom_prompts or {}
        
        # Resolve session ID (coaching -> transcript mapping)
        transcript_session_id, is_coaching = resolve_transcript_session_id(
            session_id, current_user.id, db
        )
        
        # Load segments from database using the transcript session ID
        db_segments = db.query(TranscriptSegmentModel).filter(
            TranscriptSegmentModel.session_id == transcript_session_id
        ).order_by(TranscriptSegmentModel.start_seconds).all()
        
        if not db_segments:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "No transcript segments found for this session",
                    "error_type": "no_segments",
                    "success": False
                }
            )
        
        # Fetch the session to get language information
        session = db.query(Session).filter(
            Session.id == transcript_session_id,
            Session.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Session not found",
                    "error_type": "session_not_found",
                    "success": False
                }
            )
        
        # Convert database segments to LeMUR format
        lemur_segments = []
        for segment in db_segments:
            # Map speaker_id to speaker label
            speaker_label = f"Speaker_{segment.speaker_id}" if segment.speaker_id else "A"
            
            lemur_segments.append({
                "start": int(segment.start_seconds * 1000),  # Convert to milliseconds
                "end": int(segment.end_seconds * 1000),      # Convert to milliseconds
                "speaker": speaker_label,
                "text": segment.content
            })
        
        logger.info(f"Loaded {len(lemur_segments)} segments from database for punctuation optimization")
        
        # Determine session language
        session_language = session.language or "zh-TW"
        if session_language.startswith("zh"):
            session_language = "zh-TW"
        elif session_language.startswith("en"):
            session_language = "en-US"
        
        start_time = time.time()
        
        # Apply LeMUR-based punctuation optimization only
        smoothed_result = await smooth_transcript_with_lemur(
            segments=lemur_segments,
            session_language=session_language,
            is_coaching_session=True,
            custom_prompts=custom_prompts,
            punctuation_optimization_only=True
        )
        
        # Update database segments with improved text
        segment_updates = 0
        content_comparisons_logged = 0
        for i, improved_segment in enumerate(smoothed_result.segments):
            if i < len(db_segments):
                db_segment = db_segments[i]
                
                # Debug: Log first few content comparisons to show what LeMUR changed
                if content_comparisons_logged < 3:
                    logger.info(f"📝 CONTENT COMPARISON {i+1}:")
                    logger.info(f"   Original: '{db_segment.content[:100]}{'...' if len(db_segment.content) > 100 else ''}'")
                    logger.info(f"   Improved: '{improved_segment.text[:100]}{'...' if len(improved_segment.text) > 100 else ''}'")
                    logger.info(f"   Changed: {db_segment.content != improved_segment.text}")
                    content_comparisons_logged += 1
                
                if db_segment.content != improved_segment.text:
                    db_segment.content = improved_segment.text
                    segment_updates += 1
        
        # Commit changes to database
        if segment_updates > 0:
            db.commit()
            logger.info(f"Updated {segment_updates} segments with improved punctuation")
        else:
            logger.info("No text content needed updating")
        
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
        
        logger.info(f"DB-based punctuation optimization completed: {len(response_segments)} segments, {segment_updates} updates")
        
        return LeMURSmoothingResponse(
            segments=response_segments,
            speaker_mapping=smoothed_result.speaker_mapping,
            improvements_made=smoothed_result.improvements_made + [f"Updated {segment_updates} text segments in database"],
            processing_notes=f"DB-based processing: {smoothed_result.processing_notes}",
            processing_time_ms=processing_time_ms,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DB-based punctuation optimization failed for session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Punctuation optimization failed: {str(e)}",
                "error_type": "processing_error",
                "success": False
            }
        )


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