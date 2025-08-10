"""Transcription tasks for Celery."""

import logging
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from typing import Optional

from celery import Task
from celery.exceptions import Retry
from sqlalchemy.orm import Session

from ..core.celery_app import celery_app
from ..core.database import get_db_session
from ..models.session import Session as SessionModel, SessionStatus
from ..models.transcript import TranscriptSegment as TranscriptSegmentModel
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
                session = db.query(SessionModel).filter(
                    SessionModel.id == session_id
                ).first()
                if session:
                    error_msg = f"Transcription failed: {str(exc)}"
                    session.mark_failed(error_msg)
                    db.commit()
                    logger.error(f"Session {session_id} marked as failed: {error_msg}")


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
    enable_diarization: bool = True
) -> dict:
    """
    Transcribe audio file using configured STT provider.
    
    Args:
        session_id: UUID of the session to process
        gcs_uri: Google Cloud Storage URI of audio file
        language: Language code for transcription
        enable_diarization: Enable speaker separation
        
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
        db.commit()
        
        try:
            # Create STT provider
            stt_provider = STTProviderFactory.create("google")
            
            # Perform transcription
            logger.info(f"Sending audio to STT provider: {gcs_uri}")
            result = stt_provider.transcribe(
                audio_uri=gcs_uri,
                language=language,
                enable_diarization=enable_diarization
            )
            
            logger.info(f"Transcription completed: {len(result.segments)} segments")
            
            # Save transcript segments to database
            _save_transcript_segments(db, session_uuid, result.segments)
            
            # Calculate processing duration
            processing_duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Update session as completed
            session.mark_completed(
                duration_sec=int(result.total_duration_sec),
                cost_usd=str(result.cost_usd) if result.cost_usd else None
            )
            
            # Log processing metadata
            session.transcription_job_id = self.request.id
            
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
                "duration_sec": result.total_duration_sec,
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
            db.commit()
            logger.error(f"Session {session_id} failed permanently: {error_msg}")
            raise
            
        except Exception as exc:
            # Unexpected error - retry up to max_retries
            error_msg = f"Unexpected transcription error: {exc}"
            logger.error(f"Session {session_id} error: {error_msg}", exc_info=True)
            
            if self.request.retries < self.max_retries:
                logger.info(f"Retrying session {session_id} ({self.request.retries + 1}/{self.max_retries})")
                raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
            else:
                # Max retries exceeded
                session.mark_failed(error_msg)
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
            start_sec=segment.start_sec,
            end_sec=segment.end_sec,
            content=segment.content,
            confidence=segment.confidence
        )
        db_segments.append(db_segment)
    
    # Batch insert segments
    db.add_all(db_segments)
    db.flush()  # Ensure segments are saved
    
    logger.info(f"Successfully saved {len(db_segments)} transcript segments")