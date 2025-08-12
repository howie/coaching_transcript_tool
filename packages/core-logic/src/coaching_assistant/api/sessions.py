"""Session API endpoints for audio transcription."""

from typing import List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc
from pydantic import BaseModel, Field
from datetime import datetime
import io
import json
import logging

from ..core.database import get_db
from ..models.session import Session, SessionStatus
from ..models.processing_status import ProcessingStatus
from ..models.user import User
from ..models.transcript import TranscriptSegment
from ..api.auth import get_current_user_dependency
from ..utils.gcs_uploader import GCSUploader
from ..tasks.transcription_tasks import transcribe_audio
from ..core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models
class SessionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    language: str = Field(
        default="cmn-Hant-TW", 
        pattern="^(cmn-Hant-TW|cmn-Hans-CN|zh-TW|zh-CN|en-US|en-GB|ja-JP|ko-KR|auto)$",
        max_length=20
    )


class SessionResponse(BaseModel):
    id: UUID
    title: str
    status: SessionStatus
    language: str
    audio_filename: Optional[str]
    duration_sec: Optional[int]
    duration_minutes: Optional[float]
    segments_count: int
    error_message: Optional[str]
    stt_cost_usd: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        
    @classmethod
    def from_session(cls, session: Session):
        return cls(
            id=session.id,
            title=session.title,
            status=session.status,
            language=session.language,
            audio_filename=session.audio_filename,
            duration_sec=session.duration_sec,
            duration_minutes=session.duration_minutes,
            segments_count=session.segments_count,
            error_message=session.error_message,
            stt_cost_usd=session.stt_cost_usd,
            created_at=session.created_at,
            updated_at=session.updated_at
        )


class UploadUrlResponse(BaseModel):
    upload_url: str
    gcs_path: str
    expires_at: datetime


class UploadConfirmResponse(BaseModel):
    file_exists: bool
    file_size: Optional[int]
    ready_for_transcription: bool
    message: str


class TranscriptExportResponse(BaseModel):
    format: str
    filename: str
    content: str


class SessionStatusResponse(BaseModel):
    session_id: UUID
    status: SessionStatus
    progress: int
    message: Optional[str]
    duration_processed: Optional[int]
    duration_total: Optional[int]
    started_at: Optional[datetime]
    estimated_completion: Optional[datetime]
    processing_speed: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Create a new transcription session."""
    session = Session(
        title=session_data.title,
        user_id=current_user.id,
        language=session_data.language,
        status=SessionStatus.UPLOADING
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return SessionResponse.from_session(session)


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    status: Optional[SessionStatus] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """List user's transcription sessions."""
    query = db.query(Session).filter(Session.user_id == current_user.id)
    
    if status:
        query = query.filter(Session.status == status)
    
    sessions = query.order_by(desc(Session.created_at)).offset(offset).limit(limit).all()
    
    return [SessionResponse.from_session(session) for session in sessions]


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get a specific transcription session."""
    session = db.query(Session).filter(
        Session.id == session_id,
        Session.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse.from_session(session)


@router.post("/{session_id}/upload-url", response_model=UploadUrlResponse)
async def get_upload_url(
    session_id: UUID,
    filename: str = Query(..., pattern=r"^[^\/\\]+\.(mp3|wav|flac|ogg|mp4)$"),
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get signed URL for audio file upload."""
    logger.info(f"📤 UPLOAD URL REQUEST - Session: {session_id}, User: {current_user.id}, Filename: {filename}")
    
    session = db.query(Session).filter(
        Session.id == session_id,
        Session.user_id == current_user.id
    ).first()
    
    if not session:
        logger.warning(f"❌ Upload URL request failed - Session {session_id} not found for user {current_user.id}")
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status != SessionStatus.UPLOADING:
        logger.warning(f"❌ Upload URL request failed - Session {session_id} status is {session.status.value}, expected UPLOADING")
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot upload to session with status {session.status.value}"
        )
    
    # Generate GCS path
    file_extension = filename.split('.')[-1].lower()
    gcs_filename = f"{session_id}.{file_extension}"
    gcs_path = f"audio-uploads/{current_user.id}/{gcs_filename}"
    full_gcs_path = f"gs://{settings.AUDIO_STORAGE_BUCKET}/{gcs_path}"
    
    # Map file extensions to proper MIME types
    content_type_map = {
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'flac': 'audio/flac',
        'ogg': 'audio/ogg',
        'mp4': 'audio/mp4'
    }
    content_type = content_type_map.get(file_extension, 'audio/mpeg')
    
    logger.info(f"🗂️  GCS Path: {full_gcs_path}")
    logger.info(f"🪣 Bucket: {settings.AUDIO_STORAGE_BUCKET}")
    logger.info(f"📁 Blob name: {gcs_path}")
    logger.info(f"🏷️  Content-Type: {content_type}")
    
    try:
        # Create GCS uploader and get signed URL
        uploader = GCSUploader(
            bucket_name=settings.AUDIO_STORAGE_BUCKET,
            credentials_json=settings.GOOGLE_APPLICATION_CREDENTIALS_JSON
        )
        
        logger.info(f"🔗 Generating signed upload URL with 60min expiration...")
        upload_url, expires_at = uploader.generate_signed_upload_url(
            blob_name=gcs_path,
            content_type=content_type,
            expiration_minutes=60
        )
        
        # Update session with file info
        session.audio_filename = filename
        session.gcs_audio_path = full_gcs_path
        db.commit()
        
        logger.info(f"✅ Upload URL generated successfully!")
        logger.info(f"🔗 Upload URL: {upload_url[:100]}...{upload_url[-20:]}")  # Log partial URL for security
        logger.info(f"⏰ Expires at: {expires_at}")
        logger.info(f"💾 Session updated with GCS path: {full_gcs_path}")
        
        return UploadUrlResponse(
            upload_url=upload_url,
            gcs_path=gcs_path,
            expires_at=expires_at
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to generate upload URL for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate upload URL: {str(e)}")


@router.post("/{session_id}/confirm-upload", response_model=UploadConfirmResponse)
async def confirm_upload(
    session_id: UUID,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Confirm that audio file was successfully uploaded to GCS."""
    logger.info(f"🔍 UPLOAD CONFIRMATION REQUEST - Session: {session_id}, User: {current_user.id}")
    
    session = db.query(Session).filter(
        Session.id == session_id,
        Session.user_id == current_user.id
    ).first()
    
    if not session:
        logger.warning(f"❌ Upload confirmation failed - Session {session_id} not found for user {current_user.id}")
        raise HTTPException(status_code=404, detail="Session not found")
    
    logger.info(f"📋 Session status: {session.status.value}")
    logger.info(f"🗂️  Expected GCS path: {session.gcs_audio_path}")
    
    if not session.gcs_audio_path:
        logger.warning(f"❌ No GCS path configured for session {session_id}")
        return UploadConfirmResponse(
            file_exists=False,
            file_size=None,
            ready_for_transcription=False,
            message="No upload path configured for this session"
        )
    
    try:
        # Check if file exists in GCS
        uploader = GCSUploader(
            bucket_name=settings.AUDIO_STORAGE_BUCKET,
            credentials_json=settings.GOOGLE_APPLICATION_CREDENTIALS_JSON
        )
        
        # Extract blob name from GCS path
        # Format: gs://bucket/path/to/file -> path/to/file
        blob_name = session.gcs_audio_path.replace(f"gs://{settings.AUDIO_STORAGE_BUCKET}/", "")
        
        logger.info(f"🔍 Checking file existence in GCS...")
        logger.info(f"🪣 Bucket: {settings.AUDIO_STORAGE_BUCKET}")
        logger.info(f"📄 Blob name: {blob_name}")
        logger.info(f"🔗 Full path: {session.gcs_audio_path}")
        
        file_exists, file_size = uploader.check_file_exists(blob_name)
        
        logger.info(f"📊 File check result: exists={file_exists}, size={file_size}")
        
        if file_exists:
            # Update session status to PENDING if file exists
            if session.status == SessionStatus.UPLOADING:
                session.status = SessionStatus.PENDING
                db.commit()
                logger.info(f"✅ Session status updated to PENDING")
            
            logger.info(f"✅ File confirmed for session {session_id}: {blob_name} ({file_size} bytes)")
            
            return UploadConfirmResponse(
                file_exists=True,
                file_size=file_size,
                ready_for_transcription=True,
                message=f"File uploaded successfully ({file_size} bytes). Ready for transcription."
            )
        else:
            logger.warning(f"❌ File not found for session {session_id}: {blob_name}")
            logger.info(f"💡 Suggestion: Use 'gcloud storage ls {session.gcs_audio_path}' to check manually")
            
            return UploadConfirmResponse(
                file_exists=False,
                file_size=None,
                ready_for_transcription=False,
                message=f"File not found at expected location: {blob_name}"
            )
            
    except Exception as e:
        logger.error(f"❌ Error checking file existence for session {session_id}: {e}", exc_info=True)
        return UploadConfirmResponse(
            file_exists=False,
            file_size=None,
            ready_for_transcription=False,
            message=f"Error checking file: {str(e)}"
        )


@router.post("/{session_id}/start-transcription")
async def start_transcription(
    session_id: UUID,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Start transcription processing for uploaded audio."""
    session = db.query(Session).filter(
        Session.id == session_id,
        Session.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Allow starting from UPLOADING or PENDING status
    if session.status not in [SessionStatus.UPLOADING, SessionStatus.PENDING]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start transcription for session with status {session.status.value}"
        )
    
    if not session.gcs_audio_path:
        raise HTTPException(status_code=400, detail="No audio file uploaded")
    
    # Verify file exists before starting transcription
    try:
        uploader = GCSUploader(
            bucket_name=settings.AUDIO_STORAGE_BUCKET,
            credentials_json=settings.GOOGLE_APPLICATION_CREDENTIALS_JSON
        )
        
        blob_name = session.gcs_audio_path.replace(f"gs://{settings.AUDIO_STORAGE_BUCKET}/", "")
        file_exists, file_size = uploader.check_file_exists(blob_name)
        
        if not file_exists:
            raise HTTPException(
                status_code=400, 
                detail=f"Audio file not found in storage. Please re-upload the file."
            )
        
        logger.info(f"Starting transcription for session {session_id}, file size: {file_size} bytes")
        
    except Exception as e:
        logger.error(f"Error verifying file before transcription: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to verify audio file: {str(e)}"
        )
    
    # Update status to processing
    session.update_status(SessionStatus.PROCESSING)
    db.commit()
    
    # Queue transcription task
    task = transcribe_audio.delay(
        session_id=str(session_id),
        gcs_uri=session.gcs_audio_path,
        language=session.language,
        original_filename=session.audio_filename
    )
    
    # Store task ID for tracking
    session.transcription_job_id = task.id
    db.commit()
    
    return {
        "message": "Transcription started",
        "task_id": task.id,
        "estimated_completion_minutes": 120,  # Estimate 2 hours max
        "file_size": file_size
    }


@router.get("/{session_id}/transcript")
async def export_transcript(
    session_id: UUID,
    format: str = Query("json", pattern="^(json|vtt|srt|txt)$"),
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Export transcript in various formats."""
    session = db.query(Session).filter(
        Session.id == session_id,
        Session.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status != SessionStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Transcript not available. Session status: {session.status.value}"
        )
    
    # Get transcript segments
    segments = db.query(TranscriptSegment).filter(
        TranscriptSegment.session_id == session_id
    ).order_by(TranscriptSegment.start_sec).all()
    
    if not segments:
        raise HTTPException(status_code=404, detail="No transcript segments found")
    
    # Generate transcript content based on format
    if format == "json":
        content = _export_json(session, segments)
        media_type = "application/json"
    elif format == "vtt":
        content = _export_vtt(session, segments)
        media_type = "text/vtt"
    elif format == "srt":
        content = _export_srt(session, segments)
        media_type = "text/srt"
    elif format == "txt":
        content = _export_txt(session, segments)
        media_type = "text/plain"
    else:
        raise HTTPException(status_code=400, detail="Invalid format")
    
    # Create filename
    clean_title = "".join(c for c in session.title if c.isalnum() or c in (' ', '-', '_')).strip()
    filename = f"{clean_title}.{format}"
    
    # Return as streaming response
    return StreamingResponse(
        io.StringIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(
    session_id: UUID,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get detailed processing status for a session."""
    # Check if session exists and belongs to user
    session = db.query(Session).filter(
        Session.id == session_id,
        Session.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get the processing status (should be only one per session)
    latest_status = db.query(ProcessingStatus).filter(
        ProcessingStatus.session_id == session_id
    ).first()
    
    # If no status exists, create a basic one based on session status
    if not latest_status:
        latest_status = _create_default_status(session, db)
    
    # Update progress calculation if processing
    if session.status == SessionStatus.PROCESSING:
        _update_processing_progress(session, latest_status, db)
    
    response = SessionStatusResponse(
        session_id=session.id,
        status=session.status,
        progress=latest_status.progress_percentage,
        message=latest_status.message,
        duration_processed=latest_status.duration_processed,
        duration_total=latest_status.duration_total,
        started_at=latest_status.started_at,
        estimated_completion=latest_status.estimated_completion,
        processing_speed=latest_status.processing_speed,
        created_at=latest_status.created_at,
        updated_at=latest_status.updated_at
    )
    
    # Debug logging
    logger.info(f"🔍 STATUS API DEBUG - Session {session_id}: progress={latest_status.progress_percentage}%, status={session.status}, message='{latest_status.message}'")
    
    return response


def _create_default_status(session: Session, db: DBSession) -> ProcessingStatus:
    """Create default processing status based on session status."""
    status_map = {
        SessionStatus.UPLOADING: ("pending", 0, "Waiting for file upload"),
        SessionStatus.PENDING: ("pending", 5, "File uploaded, queued for processing"),
        SessionStatus.PROCESSING: ("processing", 10, "Processing audio..."),
        SessionStatus.COMPLETED: ("completed", 100, "Transcription complete!"),
        SessionStatus.FAILED: ("failed", 0, session.error_message or "Processing failed"),
        SessionStatus.CANCELLED: ("failed", 0, "Processing cancelled")
    }
    
    status_str, progress, message = status_map.get(session.status, ("pending", 0, "Unknown status"))
    
    processing_status = ProcessingStatus(
        session_id=session.id,
        status=status_str,
        progress=progress,
        message=message,
        duration_total=session.duration_sec,
        started_at=session.created_at if session.status == SessionStatus.PROCESSING else None
    )
    
    db.add(processing_status)
    db.commit()
    db.refresh(processing_status)
    
    return processing_status


def _update_processing_progress(session: Session, status: ProcessingStatus, db: DBSession):
    """Update progress calculation for processing sessions."""
    if not status.started_at:
        status.started_at = datetime.utcnow()
    
    # Calculate elapsed time since processing started
    elapsed_seconds = (datetime.utcnow() - status.started_at).total_seconds()
    
    # Estimate progress based on time elapsed
    # Assume 4x real-time processing by default
    if session.duration_sec:
        expected_processing_time = session.duration_sec * 4  # 4x real-time
        time_based_progress = min(95, (elapsed_seconds / expected_processing_time) * 100)
        
        # Use time-based progress if we don't have actual progress
        if not status.duration_processed:
            status.progress = int(time_based_progress)
        else:
            # Combine actual progress (70%) with time-based estimate (30%)
            actual_progress = (status.duration_processed / session.duration_sec) * 100
            status.progress = int((actual_progress * 0.7) + (time_based_progress * 0.3))
        
        # Calculate processing speed
        if status.duration_processed and elapsed_seconds > 0:
            status.processing_speed = status.duration_processed / elapsed_seconds
        
        # Update estimated completion
        if status.progress < 95:
            remaining_work = max(0, expected_processing_time - elapsed_seconds)
            status.estimated_completion = datetime.utcnow() + datetime.timedelta(seconds=remaining_work)
        else:
            status.estimated_completion = datetime.utcnow() + datetime.timedelta(minutes=2)
    
    # Update message based on progress
    if status.progress < 25:
        status.message = "Starting audio processing..."
    elif status.progress < 50:
        status.message = "Processing audio segments..."
    elif status.progress < 75:
        status.message = "Analyzing speech patterns..."
    elif status.progress < 95:
        status.message = "Finalizing transcription..."
    else:
        status.message = "Almost done..."
    
    db.commit()


def _export_json(session: Session, segments: List[TranscriptSegment]) -> str:
    """Export transcript as JSON."""
    data = {
        "session_id": str(session.id),
        "title": session.title,
        "duration_sec": session.duration_sec,
        "language": session.language,
        "created_at": session.created_at.isoformat(),
        "segments": [
            {
                "speaker_id": seg.speaker_id,
                "start_sec": seg.start_sec,
                "end_sec": seg.end_sec,
                "content": seg.content,
                "confidence": seg.confidence
            }
            for seg in segments
        ]
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def _export_vtt(session: Session, segments: List[TranscriptSegment]) -> str:
    """Export transcript as WebVTT."""
    lines = ["WEBVTT", f"NOTE {session.title}", ""]
    
    for seg in segments:
        start = _format_timestamp_vtt(seg.start_sec)
        end = _format_timestamp_vtt(seg.end_sec)
        lines.append(f"{start} --> {end}")
        lines.append(f"<v Speaker {seg.speaker_id}>{seg.content}")
        lines.append("")
    
    return "\n".join(lines)


def _export_srt(session: Session, segments: List[TranscriptSegment]) -> str:
    """Export transcript as SRT."""
    lines = []
    
    for i, seg in enumerate(segments, 1):
        start = _format_timestamp_srt(seg.start_sec)
        end = _format_timestamp_srt(seg.end_sec)
        lines.append(str(i))
        lines.append(f"{start} --> {end}")
        lines.append(f"Speaker {seg.speaker_id}: {seg.content}")
        lines.append("")
    
    return "\n".join(lines)


def _export_txt(session: Session, segments: List[TranscriptSegment]) -> str:
    """Export transcript as plain text."""
    lines = [f"Transcript: {session.title}", ""]
    
    current_speaker = None
    for seg in segments:
        if seg.speaker_id != current_speaker:
            if current_speaker is not None:
                lines.append("")
            lines.append(f"Speaker {seg.speaker_id}:")
            current_speaker = seg.speaker_id
        
        lines.append(seg.content)
    
    return "\n".join(lines)


def _format_timestamp_vtt(seconds: float) -> str:
    """Format timestamp for VTT format (HH:MM:SS.mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def _format_timestamp_srt(seconds: float) -> str:
    """Format timestamp for SRT format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')