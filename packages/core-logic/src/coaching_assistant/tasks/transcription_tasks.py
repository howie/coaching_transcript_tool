"""Transcription tasks for Celery."""

import logging
from uuid import UUID
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from typing import Optional

from celery import Task
from celery.exceptions import Retry
from sqlalchemy.orm import Session
from sqlalchemy.exc import DataError, IntegrityError

from ..core.celery_app import celery_app
from ..core.database import get_db_session
from ..models.session import Session as SessionModel, SessionStatus
from ..models.transcript import TranscriptSegment as TranscriptSegmentModel
from ..models.processing_status import ProcessingStatus
from ..services import STTProviderFactory, STTProviderError, STTProviderUnavailableError
from ..core.config import settings

logger = logging.getLogger(__name__)


class TranscriptionTask(Task):
    """Base task class for transcription tasks."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        session_id = args[0] if args else None
        if session_id:
            with get_db_session() as db:
                try:
                    session = db.query(SessionModel).filter(
                        SessionModel.id == session_id
                    ).first()
                    if session:
                        error_msg = f"Transcription failed: {str(exc)}"
                        session.mark_failed(error_msg)
                        
                        # Also update processing status if exists
                        processing_status = db.query(ProcessingStatus).filter(
                            ProcessingStatus.session_id == session_id
                        ).order_by(ProcessingStatus.created_at.desc()).first()
                        
                        if processing_status:
                            processing_status.status = "failed"
                            processing_status.message = error_msg
                        
                        db.commit()
                        logger.error(f"Session {session_id} marked as failed: {error_msg}")
                except Exception as cleanup_exc:
                    db.rollback()
                    logger.error(f"Failed to mark session {session_id} as failed: {cleanup_exc}")


@celery_app.task(
    bind=True,
    base=TranscriptionTask,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    autoretry_for=(STTProviderUnavailableError,),
    retry_backoff=True,
    retry_jitter=True
)
def transcribe_audio(
    self,
    session_id: str,
    gcs_uri: str,
    language: str = "zh-TW",
    enable_diarization: bool = True,
    original_filename: str = None
) -> dict:
    """
    Transcribe audio file using configured STT provider.
    
    Args:
        session_id: UUID of the session to process
        gcs_uri: Google Cloud Storage URI of audio file
        language: Language code for transcription
        enable_diarization: Enable speaker separation
        original_filename: Original uploaded filename for format detection
        
    Returns:
        Dictionary with transcription results
    """
    session_uuid = UUID(session_id)
    start_time = datetime.utcnow()
    
    logger.info(f"Starting transcription for session {session_id}")
    
    # Get database session
    with get_db_session() as db:
        session = db.query(SessionModel).filter(
            SessionModel.id == session_uuid
        ).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Update status to processing
        session.update_status(SessionStatus.PROCESSING)
        
        # Get or create processing status record (should be only one per session)
        processing_status = db.query(ProcessingStatus).filter(
            ProcessingStatus.session_id == session_uuid
        ).first()
        
        if processing_status:
            # Update existing record
            processing_status.status = "processing"
            processing_status.progress = 0
            processing_status.message = "Initializing transcription..."
            processing_status.started_at = start_time
            processing_status.updated_at = start_time
        else:
            # Create new record if none exists
            processing_status = ProcessingStatus(
                session_id=session_uuid,
                status="processing",
                progress=0,
                message="Initializing transcription...",
                started_at=start_time
            )
            db.add(processing_status)
        
        db.commit()
        
        try:
            # Create STT provider
            stt_provider = STTProviderFactory.create("google")
            
            # Update progress: STT provider initialized
            processing_status.update_progress(10, "Connecting to speech service...")
            db.commit()
            
            # Perform transcription with progress callback
            logger.info(f"Sending audio to STT provider: {gcs_uri}")
            processing_status.update_progress(25, "Processing audio with Google STT...")
            db.commit()
            
            def update_transcription_progress(progress_percentage, message, elapsed_minutes):
                """Callback to update transcription progress in database."""
                try:
                    # Map progress from 25% (start) to 75% (just before saving)
                    # This reserves 25% for initial setup and 25% for saving
                    mapped_progress = 25 + (progress_percentage * 0.5)  # 25% + (0-100% * 50%)
                    
                    progress_message = f"Processing audio... {elapsed_minutes:.1f} min elapsed"
                    if progress_percentage > 90:
                        progress_message = "Almost done processing audio..."
                    
                    # Re-query the processing status to ensure we have the latest from DB
                    current_status = db.query(ProcessingStatus).filter(
                        ProcessingStatus.session_id == session_uuid
                    ).first()
                    
                    if current_status:
                        current_status.update_progress(int(mapped_progress), progress_message)
                        db.commit()
                        logger.info(f"STT Progress: {mapped_progress:.1f}% - {progress_message} (DB updated)")
                    else:
                        logger.warning(f"Processing status not found for session {session_uuid}")
                    
                except Exception as e:
                    db.rollback()
                    logger.warning(f"Failed to update progress: {e}")
            
            result = stt_provider.transcribe(
                audio_uri=gcs_uri,
                language=language,
                enable_diarization=enable_diarization,
                original_filename=original_filename,
                progress_callback=update_transcription_progress
            )
            
            logger.info(f"Transcription completed: {len(result.segments)} segments")
            
            # Update progress: transcription completed, now saving
            processing_status.update_progress(80, "Saving transcript segments...")
            db.commit()
            
            # Save transcript segments to database
            _save_transcript_segments(db, session_uuid, result.segments)
            
            # Calculate processing duration
            processing_duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Update progress: finalizing
            processing_status.update_progress(95, "Finalizing transcription...")
            processing_status.duration_total = int(result.total_duration_sec)
            processing_status.duration_processed = int(result.total_duration_sec)
            db.commit()
            
            # Calculate actual duration from segments
            actual_duration_sec = _calculate_actual_duration(db, session_uuid)
            
            # Format cost to fit VARCHAR(10) constraint
            formatted_cost = None
            if result.cost_usd:
                cost_decimal = Decimal(str(result.cost_usd))
                cost_rounded = cost_decimal.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                formatted_cost = f"{cost_rounded:.6f}"
            
            # Update session as completed
            session.mark_completed(
                duration_sec=actual_duration_sec,
                cost_usd=formatted_cost
            )
            
            # Log processing metadata
            session.transcription_job_id = self.request.id
            
            # Final progress update
            processing_status.update_progress(100, "Transcription completed successfully!")
            processing_status.status = "completed"
            
            db.commit()
            
            logger.info(
                f"Session {session_id} completed successfully: "
                f"{len(result.segments)} segments, "
                f"{result.total_duration_sec:.1f}s audio, "
                f"{processing_duration:.1f}s processing time"
            )
            
            return {
                "session_id": session_id,
                "status": "completed",
                "segments_count": len(result.segments),
                "duration_seconds": result.total_duration_sec,
                "processing_time_sec": processing_duration,
                "cost_usd": float(result.cost_usd) if result.cost_usd else 0.0,
                "language_code": result.language_code
            }
            
        except STTProviderUnavailableError as exc:
            # This will trigger automatic retry
            logger.warning(f"STT provider unavailable, retrying: {exc}")
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
            
        except STTProviderError as exc:
            # Permanent failure - don't retry
            error_msg = f"STT provider error: {exc}"
            session.mark_failed(error_msg)
            processing_status.status = "failed"
            processing_status.message = error_msg
            db.commit()
            logger.error(f"Session {session_id} failed permanently: {error_msg}")
            raise
            
        except (DataError, IntegrityError) as exc:
            # Database constraint errors - don't retry, rollback and fail
            error_msg = f"Database constraint error: {exc}"
            logger.error(f"Session {session_id} database error: {error_msg}")
            db.rollback()  # Important: rollback before trying to update
            
            session.mark_failed(error_msg)
            processing_status.status = "failed"
            processing_status.message = error_msg
            db.commit()
            raise
            
        except Exception as exc:
            # Unexpected error - retry up to max_retries
            error_msg = f"Unexpected transcription error: {exc}"
            logger.error(f"Session {session_id} error: {error_msg}", exc_info=True)
            
            if self.request.retries < self.max_retries:
                logger.info(f"Retrying session {session_id} ({self.request.retries + 1}/{self.max_retries})")
                raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
            else:
                # Max retries exceeded - rollback before final failure
                db.rollback()
                session.mark_failed(error_msg)
                processing_status.status = "failed"
                processing_status.message = error_msg
                db.commit()
                raise


def _save_transcript_segments(
    db: Session, 
    session_id: UUID, 
    segments: list
) -> None:
    """Save transcript segments to database."""
    logger.info(f"Saving {len(segments)} transcript segments for session {session_id}")
    
    db_segments = []
    for segment in segments:
        db_segment = TranscriptSegmentModel(
            session_id=session_id,
            speaker_id=segment.speaker_id,
            start_seconds=segment.start_seconds,
            end_seconds=segment.end_seconds,
            content=segment.content,
            confidence=segment.confidence
        )
        db_segments.append(db_segment)
    
    # Batch insert segments
    db.add_all(db_segments)
    db.flush()  # Ensure segments are saved
    
    logger.info(f"Successfully saved {len(db_segments)} transcript segments")


def _calculate_actual_duration(db: Session, session_id: UUID) -> int:
    """Calculate actual duration from transcript segments."""
    # Get the maximum end_sec from all segments
    max_end_sec = db.query(TranscriptSegmentModel.end_seconds).filter(
        TranscriptSegmentModel.session_id == session_id
    ).order_by(TranscriptSegmentModel.end_seconds.desc()).first()
    
    if max_end_sec and max_end_sec[0]:
        return int(max_end_sec[0])
    
    # Fallback to 0 if no segments found
    return 0