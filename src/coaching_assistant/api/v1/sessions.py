"""Session API endpoints for audio transcription."""

from typing import List, Optional
from uuid import UUID, uuid4
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    UploadFile,
    File as FastAPIFile,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as DBSession  # Still needed for role management endpoints
from sqlalchemy import desc
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import io
import json
import logging
import re

from ...core.database import get_db  # Still needed for role management endpoints
from ...core.models.session import SessionStatus
# TEMPORARY: Still needed for legacy endpoints that haven't been migrated to Clean Architecture
from ...models.session import Session
from ...models.transcript import TranscriptSegment
from ...models.user import User
from .auth import get_current_user_dependency
from ...api.v1.dependencies import (
    get_session_creation_use_case,
    get_session_retrieval_use_case,
    get_session_status_update_use_case,
    get_session_transcript_update_use_case,
    get_session_upload_management_use_case,
    get_session_transcription_management_use_case,
    get_session_export_use_case,
    get_session_status_retrieval_use_case,
    get_session_transcript_upload_use_case,
    get_speaker_role_assignment_use_case,
    get_segment_role_assignment_use_case,
    get_speaker_role_retrieval_use_case,
)
from ...utils.gcs_uploader import GCSUploader
from ...tasks.transcription_tasks import transcribe_audio
from ...core.config import settings
from ...exporters.excel import generate_excel
from ...services.usage_tracking import UsageTrackingService
from ...services.plan_limits import get_global_plan_limits

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic models
class SessionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    language: str = Field(
        default="cmn-Hant-TW",
        pattern="^(cmn-Hant-TW|cmn-Hans-CN|zh-TW|zh-CN|en-US|en-GB|ja-JP|ko-KR|auto)$",
        max_length=20,
    )
    stt_provider: str = Field(
        default="auto",
        pattern="^(auto|google|assemblyai)$",
        description="STT provider to use ('auto' uses settings default, 'google', or 'assemblyai')",
    )


class SessionResponse(BaseModel):
    id: UUID
    title: str
    status: SessionStatus
    language: str
    stt_provider: Optional[str] = None
    audio_filename: Optional[str]
    duration_seconds: Optional[int]
    duration_minutes: Optional[float]
    segments_count: int
    error_message: Optional[str]
    stt_cost_usd: Optional[str]
    provider_metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_session(cls, session: Session):
        # Calculate duration_minutes from duration_seconds for legacy compatibility
        duration_minutes = None
        if session.duration_seconds:
            duration_minutes = round(session.duration_seconds / 60, 1)

        return cls(
            id=session.id,
            title=session.title,
            status=session.status,
            language=session.language,
            stt_provider=session.stt_provider,
            audio_filename=session.audio_filename,
            duration_seconds=session.duration_seconds,
            duration_minutes=duration_minutes,
            segments_count=getattr(session, "segments_count", 0),  # Default to 0 for legacy compatibility
            error_message=session.error_message,
            stt_cost_usd=session.stt_cost_usd,
            provider_metadata=getattr(session, "provider_metadata", None),
            created_at=session.created_at,
            updated_at=session.updated_at,
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
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    processing_speed: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProviderInfo(BaseModel):
    name: str
    display_name: str
    supported_languages: List[str]
    features: List[str]
    cost_per_minute: Optional[str] = None


class ProvidersResponse(BaseModel):
    available_providers: List[ProviderInfo]
    default_provider: str


@router.post("", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user_dependency),
    session_creation_use_case=Depends(get_session_creation_use_case),
):
    """Create a new transcription session."""
    session = session_creation_use_case.execute(
        user_id=current_user.id,
        title=session_data.title,
        language=session_data.language,
        stt_provider=session_data.stt_provider,
    )
    return SessionResponse.from_session(session)


@router.get("/providers", response_model=ProvidersResponse)
async def get_available_providers():
    """Get available STT providers and their information."""
    providers_info = []

    # Google STT provider info
    google_info = ProviderInfo(
        name="google",
        display_name="Google Speech-to-Text",
        supported_languages=[
            "cmn-Hant-TW",
            "cmn-Hans-CN",
            "en-US",
            "en-GB",
            "ja-JP",
            "ko-KR",
        ],
        features=[
            "Speaker Diarization",
            "High Accuracy",
            "Multiple Languages",
        ],
        cost_per_minute="~$0.024",
    )
    providers_info.append(google_info)

    # AssemblyAI provider info
    assemblyai_info = ProviderInfo(
        name="assemblyai",
        display_name="AssemblyAI",
        supported_languages=["en", "zh", "ja"],
        features=[
            "Auto Speaker Diarization",
            "Coaching Analysis",
            "Fast Processing",
        ],
        cost_per_minute="~$0.015-0.024",
    )
    providers_info.append(assemblyai_info)

    # Get default provider from settings
    default_provider = getattr(settings, "STT_PROVIDER", "google")

    return ProvidersResponse(
        available_providers=providers_info, default_provider=default_provider
    )


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    status: Optional[SessionStatus] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user_dependency),
    session_retrieval_use_case=Depends(get_session_retrieval_use_case),
):
    """List user's transcription sessions."""
    sessions = session_retrieval_use_case.get_user_sessions(
        user_id=current_user.id,
        status=status,
        limit=limit,
        offset=offset,
    )

    return [SessionResponse.from_session(session) for session in sessions]


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user_dependency),
    session_retrieval_use_case=Depends(get_session_retrieval_use_case),
):
    """Get a specific transcription session."""
    session = session_retrieval_use_case.get_session_by_id(
        session_id=session_id,
        user_id=current_user.id,
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse.from_session(session)


@router.post("/{session_id}/upload-url", response_model=UploadUrlResponse)
async def get_upload_url(
    session_id: UUID,
    filename: str = Query(
        ..., pattern=r"^[^\/\\]+\.(mp3|wav|flac|ogg|mp4|m4a)$"
    ),
    file_size_mb: float = Query(
        ..., description="File size in MB for plan limit validation"
    ),
    current_user: User = Depends(get_current_user_dependency),
    upload_management_use_case=Depends(get_session_upload_management_use_case),
):
    """Get signed URL for audio file upload."""
    from ...exceptions import DomainException

    logger.info(
        f"📤 UPLOAD URL REQUEST - Session: {session_id}, User: {current_user.id}, Filename: {filename}, Size: {file_size_mb}MB"
    )

    try:
        # Use case validates plan limits, session ownership, and status
        result = upload_management_use_case.generate_upload_url(
            session_id=session_id,
            user_id=current_user.id,
            filename=filename,
            file_size_mb=file_size_mb,
        )

        session = result["session"]
        user_plan = result["user_plan"]

        # Generate GCS path
        file_extension = filename.split(".")[-1].lower()
        gcs_filename = f"{session_id}.{file_extension}"
        gcs_path = f"audio-uploads/{current_user.id}/{gcs_filename}"
        full_gcs_path = f"gs://{settings.AUDIO_STORAGE_BUCKET}/{gcs_path}"

        # Map file extensions to proper MIME types
        content_type_map = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "flac": "audio/flac",
            "ogg": "audio/ogg",
            "mp4": "audio/mp4",
            "m4a": "audio/mp4",  # M4A uses same MIME type as MP4
        }
        content_type = content_type_map.get(file_extension, "audio/mpeg")

        logger.info(f"🗂️  GCS Path: {full_gcs_path}")
        logger.info(f"🪣 Bucket: {settings.AUDIO_STORAGE_BUCKET}")
        logger.info(f"📁 Blob name: {gcs_path}")
        logger.info(f"🏷️  Content-Type: {content_type}")

        # Create GCS uploader and get signed URL
        uploader = GCSUploader(
            bucket_name=settings.AUDIO_STORAGE_BUCKET,
            credentials_json=settings.GOOGLE_APPLICATION_CREDENTIALS_JSON,
        )

        logger.info(f"🔗 Generating signed upload URL with 60min expiration...")
        upload_url, expires_at = uploader.generate_signed_upload_url(
            blob_name=gcs_path,
            content_type=content_type,
            expiration_minutes=60,
        )

        # Update session with file info using use case
        upload_management_use_case.update_session_file_info(
            session_id=session_id,
            user_id=current_user.id,
            audio_filename=filename,
            gcs_audio_path=full_gcs_path,
        )

        logger.info(f"✅ Upload URL generated successfully!")
        logger.info(f"🔗 Upload URL: {upload_url[:100]}...{upload_url[-20:]}")
        logger.info(f"⏰ Expires at: {expires_at}")
        logger.info(f"💾 Session updated with GCS path: {full_gcs_path}")

        return UploadUrlResponse(
            upload_url=upload_url, gcs_path=gcs_path, expires_at=expires_at
        )

    except DomainException as e:
        # Handle domain exceptions (plan limits, status validation)
        if "File size" in str(e) and "exceeds plan limit" in str(e):
            raise HTTPException(
                status_code=413,
                detail={
                    "error": "file_size_exceeded",
                    "message": str(e),
                    "file_size_mb": file_size_mb,
                    "plan": (current_user.plan.value if current_user.plan else "free"),
                },
            )
        elif "Cannot upload to session" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        # Handle session not found
        if "Session not found" in str(e):
            logger.warning(f"❌ Upload URL request failed - Session {session_id} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Session not found")
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to generate upload URL for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate upload URL: {str(e)}")


@router.post(
    "/{session_id}/confirm-upload", response_model=UploadConfirmResponse
)
async def confirm_upload(
    session_id: UUID,
    current_user: User = Depends(get_current_user_dependency),
    upload_management_use_case=Depends(get_session_upload_management_use_case),
):
    """Confirm that audio file was successfully uploaded to GCS."""
    logger.info(
        f"🔍 UPLOAD CONFIRMATION REQUEST - Session: {session_id}, User: {current_user.id}"
    )

    try:
        # Use case validates session ownership and gets session info
        result = upload_management_use_case.confirm_upload(
            session_id=session_id,
            user_id=current_user.id,
        )

        session = result["session"]
        gcs_path = result["gcs_path"]

        logger.info(f"📋 Session status: {session.status.value}")
        logger.info(f"🗂️  Expected GCS path: {gcs_path}")

        if not gcs_path:
            logger.warning(f"❌ No GCS path configured for session {session_id}")
            return UploadConfirmResponse(
                file_exists=False,
                file_size=None,
                ready_for_transcription=False,
                message="No upload path configured for this session",
            )

        # Check if file exists in GCS
        uploader = GCSUploader(
            bucket_name=settings.AUDIO_STORAGE_BUCKET,
            credentials_json=settings.GOOGLE_APPLICATION_CREDENTIALS_JSON,
        )

        # Extract blob name from GCS path
        # Format: gs://bucket/path/to/file -> path/to/file
        blob_name = gcs_path.replace(f"gs://{settings.AUDIO_STORAGE_BUCKET}/", "")

        logger.info(f"🔍 Checking file existence in GCS...")
        logger.info(f"🪣 Bucket: {settings.AUDIO_STORAGE_BUCKET}")
        logger.info(f"📄 Blob name: {blob_name}")
        logger.info(f"🔗 Full path: {gcs_path}")

        file_exists, file_size = uploader.check_file_exists(blob_name)

        logger.info(f"📊 File check result: exists={file_exists}, size={file_size}")

        if file_exists:
            # Update session status to PENDING if file exists using use case
            upload_management_use_case.mark_upload_complete(
                session_id=session_id,
                user_id=current_user.id,
            )
            logger.info(f"✅ Session status updated to PENDING")

            logger.info(
                f"✅ File confirmed for session {session_id}: {blob_name} ({file_size} bytes)"
            )

            return UploadConfirmResponse(
                file_exists=True,
                file_size=file_size,
                ready_for_transcription=True,
                message=f"File uploaded successfully ({file_size} bytes). Ready for transcription.",
            )
        else:
            logger.warning(f"❌ File not found for session {session_id}: {blob_name}")
            logger.info(f"💡 Suggestion: Use 'gcloud storage ls {gcs_path}' to check manually")

            return UploadConfirmResponse(
                file_exists=False,
                file_size=None,
                ready_for_transcription=False,
                message=f"File not found at expected location: {blob_name}",
            )

    except ValueError as e:
        # Handle session not found
        if "Session not found" in str(e):
            logger.warning(
                f"❌ Upload confirmation failed - Session {session_id} not found for user {current_user.id}"
            )
            raise HTTPException(status_code=404, detail="Session not found")
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"❌ Error checking file existence for session {session_id}: {e}",
            exc_info=True,
        )
        return UploadConfirmResponse(
            file_exists=False,
            file_size=None,
            ready_for_transcription=False,
            message=f"Error checking file: {str(e)}",
        )


@router.post("/{session_id}/start-transcription")
async def start_transcription(
    session_id: UUID,
    current_user: User = Depends(get_current_user_dependency),
    transcription_management_use_case=Depends(get_session_transcription_management_use_case),
):
    """Start transcription processing for uploaded audio."""
    # Note: Transcription limits removed in Phase 2 - now unlimited
    # Only minutes-based limits are enforced
    from ...exceptions import DomainException

    try:
        # Use case validates session ownership, status, and file existence
        transcription_data = transcription_management_use_case.start_transcription(
            session_id=session_id,
            user_id=current_user.id,
        )

        # Verify file exists before starting transcription
        gcs_uri = transcription_data["gcs_uri"]
        blob_name = gcs_uri.replace(f"gs://{settings.AUDIO_STORAGE_BUCKET}/", "")

        uploader = GCSUploader(
            bucket_name=settings.AUDIO_STORAGE_BUCKET,
            credentials_json=settings.GOOGLE_APPLICATION_CREDENTIALS_JSON,
        )

        file_exists, file_size = uploader.check_file_exists(blob_name)

        if not file_exists:
            raise HTTPException(
                status_code=400,
                detail="Audio file not found in storage. Please re-upload the file.",
            )

        logger.info(
            f"Starting transcription for session {session_id}, file size: {file_size} bytes"
        )

        # Queue transcription task
        task = transcribe_audio.delay(
            session_id=transcription_data["session_id"],
            gcs_uri=transcription_data["gcs_uri"],
            language=transcription_data["language"],
            original_filename=transcription_data["original_filename"],
        )

        # Store task ID for tracking using use case
        transcription_management_use_case.update_transcription_job_id(
            session_id=session_id,
            user_id=current_user.id,
            job_id=task.id,
        )

        return {
            "message": "Transcription started",
            "task_id": task.id,
            "estimated_completion_minutes": 120,  # Estimate 2 hours max
            "file_size": file_size,
        }

    except DomainException as e:
        if "Cannot start transcription" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        elif "No audio file uploaded" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        if "Session not found" in str(e):
            raise HTTPException(status_code=404, detail="Session not found")
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error verifying file before transcription: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to verify audio file: {str(e)}"
        )


@router.post("/{session_id}/retry-transcription")
async def retry_transcription(
    session_id: UUID,
    current_user: User = Depends(get_current_user_dependency),
    transcription_management_use_case=Depends(get_session_transcription_management_use_case),
):
    """Retry transcription for failed sessions."""
    from ...exceptions import DomainException

    try:
        # Use case validates session ownership, status, and clears existing data
        transcription_data = transcription_management_use_case.retry_transcription(
            session_id=session_id,
            user_id=current_user.id,
        )

        # Verify file still exists before retrying
        gcs_uri = transcription_data["gcs_uri"]
        blob_name = gcs_uri.replace(f"gs://{settings.AUDIO_STORAGE_BUCKET}/", "")

        uploader = GCSUploader(
            bucket_name=settings.AUDIO_STORAGE_BUCKET,
            credentials_json=settings.GOOGLE_APPLICATION_CREDENTIALS_JSON,
        )

        file_exists, file_size = uploader.check_file_exists(blob_name)

        if not file_exists:
            # File missing - use case should handle resetting session
            raise HTTPException(
                status_code=400,
                detail="Audio file no longer exists. Session reset to allow re-upload.",
            )

        logger.info(
            f"Retrying transcription for session {session_id}, file size: {file_size} bytes"
        )

        # Queue transcription task with retry attempt tracking
        task = transcribe_audio.delay(
            session_id=transcription_data["session_id"],
            gcs_uri=transcription_data["gcs_uri"],
            language=transcription_data["language"],
            original_filename=transcription_data["original_filename"],
        )

        # Store new task ID using use case
        transcription_management_use_case.update_transcription_job_id(
            session_id=session_id,
            user_id=current_user.id,
            job_id=task.id,
        )

        return {
            "message": "Transcription retry started",
            "task_id": task.id,
            "estimated_completion_minutes": 120,
            "file_size": file_size,
            "retry": True,
        }

    except DomainException as e:
        if "Cannot retry transcription" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        elif "No audio file found" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        if "Session not found" in str(e):
            raise HTTPException(status_code=404, detail="Session not found")
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error verifying file before retry: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to verify audio file: {str(e)}"
        )


@router.get("/{session_id}/transcript")
async def export_transcript(
    session_id: UUID,
    format: str = Query("json", pattern="^(json|vtt|srt|txt|xlsx)$"),
    current_user: User = Depends(get_current_user_dependency),
    export_use_case=Depends(get_session_export_use_case),
    speaker_role_use_case=Depends(get_speaker_role_retrieval_use_case),
):
    """Export transcript in various formats."""
    from ...exceptions import DomainException

    try:
        # Use case validates session ownership, status, and gets transcript data
        export_data = export_use_case.export_transcript(
            session_id=session_id,
            user_id=current_user.id,
            format=format,
        )

        session = export_data["session"]
        segments = export_data["segments"]

        # Generate transcript content based on format
        if format == "json":
            content = _export_json(session, segments, speaker_role_use_case, current_user.id)
            media_type = "application/json"
            response_io = io.StringIO(content)
        elif format == "vtt":
            content = _export_vtt(session, segments, speaker_role_use_case, current_user.id)
            media_type = "text/vtt"
            response_io = io.StringIO(content)
        elif format == "srt":
            content = _export_srt(session, segments, speaker_role_use_case, current_user.id)
            media_type = "text/srt"
            response_io = io.StringIO(content)
        elif format == "txt":
            content = _export_txt(session, segments, speaker_role_use_case, current_user.id)
            media_type = "text/plain"
            response_io = io.StringIO(content)
        elif format == "xlsx":
            excel_buffer = _export_xlsx(session, segments, speaker_role_use_case, current_user.id)
            media_type = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            response_io = excel_buffer
        else:
            raise HTTPException(status_code=400, detail="Invalid format")

        # Create filename
        clean_title = "".join(
            c for c in session.title if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        filename = f"{clean_title}.{format}"

        # Return as streaming response
        return StreamingResponse(
            response_io,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except DomainException as e:
        if "Transcript not available" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        elif "No transcript segments found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        elif "Invalid format" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        if "Session not found" in str(e):
            raise HTTPException(status_code=404, detail="Session not found")
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in export_transcript for session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while exporting transcript"
        )


@router.get("/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(
    session_id: UUID,
    current_user: User = Depends(get_current_user_dependency),
    status_retrieval_use_case=Depends(get_session_status_retrieval_use_case),
):
    """Get detailed processing status for a session."""
    try:
        # Use case validates session ownership and provides processing status
        status_data = status_retrieval_use_case.get_detailed_status(
            session_id=session_id,
            user_id=current_user.id,
        )

        session = status_data["session"]
        processing_status = status_data["processing_status"]

        response = SessionStatusResponse(
            session_id=session.id,
            status=session.status,
            progress=processing_status["progress_percentage"],
            message=processing_status["message"],
            duration_processed=processing_status["duration_processed"],
            duration_total=processing_status["duration_total"],
            started_at=processing_status["started_at"],
            estimated_completion=processing_status["estimated_completion"],
            processing_speed=processing_status["processing_speed"],
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

        # Debug logging
        logger.info(
            f"🔍 STATUS API DEBUG - Session {session_id}: progress={processing_status['progress_percentage']}%, status={session.status}, message='{processing_status['message']}'"
        )

        return response

    except ValueError as e:
        if "Session not found" in str(e):
            raise HTTPException(status_code=404, detail="Session not found")
        else:
            raise HTTPException(status_code=400, detail=str(e))


class SpeakerRoleUpdateRequest(BaseModel):
    speaker_roles: dict[int, str]


class SegmentRoleUpdateRequest(BaseModel):
    segment_roles: dict[str, str]  # segment_id -> role


@router.patch("/{session_id}/speaker-roles")
async def update_speaker_roles(
    session_id: UUID,
    request: SpeakerRoleUpdateRequest,
    current_user: User = Depends(get_current_user_dependency),
    speaker_role_use_case = Depends(get_speaker_role_assignment_use_case),
):
    """Update speaker role assignments for a session."""
    try:
        result = speaker_role_use_case.execute(
            session_id=session_id,
            user_id=current_user.id,
            speaker_roles=request.speaker_roles,
        )
        return result
    except ValueError as e:
        # Convert domain exceptions to appropriate HTTP exceptions
        error_msg = str(e)
        if "Session not found" in error_msg:
            raise HTTPException(status_code=404, detail="Session not found")
        elif "Access denied" in error_msg:
            raise HTTPException(status_code=403, detail="Access denied")
        elif "Cannot update speaker roles" in error_msg or "Session status" in error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        elif "Invalid" in error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        else:
            raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{session_id}/segment-roles")
async def update_segment_roles(
    session_id: UUID,
    request: SegmentRoleUpdateRequest,
    current_user: User = Depends(get_current_user_dependency),
    segment_role_use_case = Depends(get_segment_role_assignment_use_case),
):
    """Update individual segment role assignments for a session."""
    try:
        result = segment_role_use_case.execute(
            session_id=session_id,
            user_id=current_user.id,
            segment_roles=request.segment_roles,
        )
        return result
    except ValueError as e:
        # Convert domain exceptions to appropriate HTTP exceptions
        error_msg = str(e)
        if "Session not found" in error_msg:
            raise HTTPException(status_code=404, detail="Session not found")
        elif "Access denied" in error_msg:
            raise HTTPException(status_code=403, detail="Access denied")
        elif "Cannot update segment roles" in error_msg or "Session status" in error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        elif "Invalid" in error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        else:
            raise HTTPException(status_code=500, detail="Internal server error")




def _export_json(
    session: Session, segments: List[TranscriptSegment], speaker_role_use_case, user_id: UUID
) -> str:
    """Export transcript as JSON."""
    # Get role assignments using the speaker role use case
    role_assignments = speaker_role_use_case.get_session_speaker_roles(
        session_id=session.id, user_id=user_id
    )

    # Get segment-level role assignments
    segment_roles = speaker_role_use_case.get_segment_roles(
        session_id=session.id, user_id=user_id
    )

    data = {
        "session_id": str(session.id),
        "title": session.title,
        "duration_seconds": session.duration_seconds,
        "language": session.language,
        "created_at": session.created_at.isoformat(),
        "role_assignments": role_assignments,  # Speaker-level roles (for compatibility)
        "segment_roles": segment_roles,  # Segment-level roles (new)
        "segments": [
            {
                "id": str(seg.id),
                "speaker_id": seg.speaker_id,
                "start_sec": seg.start_seconds,  # Frontend expects start_sec
                "end_sec": seg.end_seconds,  # Frontend expects end_sec
                "content": seg.content,
                "confidence": seg.confidence,
                "role": segment_roles.get(
                    str(seg.id),
                    role_assignments.get(seg.speaker_id, "unknown"),
                ),
            }
            for seg in segments
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def _export_vtt(
    session: Session, segments: List[TranscriptSegment], speaker_role_use_case, user_id: UUID
) -> str:
    """Export transcript as WebVTT."""
    # Get role assignments using the speaker role use case
    role_assignments_raw = speaker_role_use_case.get_session_speaker_roles(
        session_id=session.id, user_id=user_id
    )
    role_assignments = {
        speaker_id: ("教練" if role == "coach" else "客戶")
        for speaker_id, role in role_assignments_raw.items()
    }

    # Get segment-level role assignments
    segment_roles_raw = speaker_role_use_case.get_segment_roles(
        session_id=session.id, user_id=user_id
    )
    segment_roles = {
        segment_id: ("教練" if role == "coach" else "客戶")
        for segment_id, role in segment_roles_raw.items()
    }

    lines = ["WEBVTT", f"NOTE {session.title}", ""]

    for seg in segments:
        start = _format_timestamp_vtt(seg.start_seconds)
        end = _format_timestamp_vtt(seg.end_seconds)
        # Use segment-level role if available, otherwise use speaker-level role
        speaker_label = segment_roles.get(
            str(seg.id),
            role_assignments.get(seg.speaker_id, f"Speaker {seg.speaker_id}"),
        )
        lines.append(f"{start} --> {end}")
        lines.append(f"<v {speaker_label}>{seg.content}")
        lines.append("")

    return "\n".join(lines)


def _export_srt(
    session: Session, segments: List[TranscriptSegment], speaker_role_use_case, user_id: UUID
) -> str:
    """Export transcript as SRT."""
    # Get role assignments using the speaker role use case
    role_assignments_raw = speaker_role_use_case.get_session_speaker_roles(
        session_id=session.id, user_id=user_id
    )
    role_assignments = {
        speaker_id: ("教練" if role == "coach" else "客戶")
        for speaker_id, role in role_assignments_raw.items()
    }

    # Get segment-level role assignments
    segment_roles_raw = speaker_role_use_case.get_segment_roles(
        session_id=session.id, user_id=user_id
    )
    segment_roles = {
        segment_id: ("教練" if role == "coach" else "客戶")
        for segment_id, role in segment_roles_raw.items()
    }

    lines = []

    for i, seg in enumerate(segments, 1):
        start = _format_timestamp_srt(seg.start_seconds)
        end = _format_timestamp_srt(seg.end_seconds)
        # Use segment-level role if available, otherwise use speaker-level role
        speaker_label = segment_roles.get(
            str(seg.id),
            role_assignments.get(seg.speaker_id, f"Speaker {seg.speaker_id}"),
        )
        lines.append(str(i))
        lines.append(f"{start} --> {end}")
        lines.append(f"{speaker_label}: {seg.content}")
        lines.append("")

    return "\n".join(lines)


def _export_txt(
    session: Session, segments: List[TranscriptSegment], speaker_role_use_case, user_id: UUID
) -> str:
    """Export transcript as plain text."""
    # Get role assignments using the speaker role use case
    role_assignments_raw = speaker_role_use_case.get_session_speaker_roles(
        session_id=session.id, user_id=user_id
    )
    role_assignments = {
        speaker_id: ("教練" if role == "coach" else "客戶")
        for speaker_id, role in role_assignments_raw.items()
    }

    # Get segment-level role assignments
    segment_roles_raw = speaker_role_use_case.get_segment_roles(
        session_id=session.id, user_id=user_id
    )
    segment_roles = {
        segment_id: ("教練" if role == "coach" else "客戶")
        for segment_id, role in segment_roles_raw.items()
    }

    lines = [f"Transcript: {session.title}", ""]

    current_speaker_label = None
    for seg in segments:
        # Use segment-level role if available, otherwise use speaker-level role
        speaker_label = segment_roles.get(
            str(seg.id),
            role_assignments.get(seg.speaker_id, f"Speaker {seg.speaker_id}"),
        )

        if speaker_label != current_speaker_label:
            if current_speaker_label is not None:
                lines.append("")
            lines.append(f"{speaker_label}:")
            current_speaker_label = speaker_label

        lines.append(seg.content)

    return "\n".join(lines)


def _export_xlsx(
    session: Session, segments: List[TranscriptSegment], speaker_role_use_case, user_id: UUID
) -> io.BytesIO:
    """Export transcript as Excel file."""
    # Get role assignments using the speaker role use case
    role_assignments_raw = speaker_role_use_case.get_session_speaker_roles(
        session_id=session.id, user_id=user_id
    )
    # Normalize to English labels for the Excel dataset; map later to Chinese
    role_assignments = {
        speaker_id: ("Coach" if role == "coach" else "Client")
        for speaker_id, role in role_assignments_raw.items()
    }

    # Get segment-level role assignments
    segment_roles_raw = speaker_role_use_case.get_segment_roles(
        session_id=session.id, user_id=user_id
    )
    segment_roles = {
        segment_id: ("Coach" if role == "coach" else "Client")
        for segment_id, role in segment_roles_raw.items()
    }

    # Prepare data for Excel export
    data = []
    for seg in segments:
        # Use segment-level role if available, otherwise use speaker-level role
        speaker_role = segment_roles.get(
            str(seg.id), role_assignments.get(seg.speaker_id)
        )

        # Convert role to proper Chinese labels with fallback
        if speaker_role == "Coach":
            speaker_label = "教練"
        elif speaker_role == "Client":
            speaker_label = "客戶"
        elif speaker_role == "教練":
            speaker_label = "教練"
        elif speaker_role == "客戶":
            speaker_label = "客戶"
        else:
            # Fallback: assume speaker_id 1 is coach, others are clients
            speaker_label = "教練" if seg.speaker_id == 1 else "客戶"

        # Format timestamp - only show start time
        start_time = _format_timestamp_vtt(seg.start_seconds)

        data.append(
            {
                "time": start_time,
                "speaker": speaker_label,
                "content": seg.content,
            }
        )

    # Generate Excel file using the existing excel exporter
    return generate_excel(data)


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
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace(".", ",")


@router.post("/{session_id}/transcript")
async def upload_session_transcript(
    session_id: UUID,
    file: UploadFile = FastAPIFile(...),
    current_user: User = Depends(get_current_user_dependency),
    transcript_upload_use_case=Depends(get_session_transcript_upload_use_case),
):
    """Upload a VTT or SRT transcript file directly to a session."""
    from ...exceptions import DomainException

    logger.info(
        f"🔍 Transcript upload request: session_id={session_id}, user_id={current_user.id}, filename={file.filename}"
    )

    try:
        # Read file content
        content = await file.read()
        content_str = content.decode("utf-8")

        # Use case validates session ownership and file format, parses content
        upload_result = transcript_upload_use_case.upload_transcript_file(
            session_id=session_id,
            user_id=current_user.id,
            filename=file.filename or "transcript",
            content=content_str,
        )

        segments_data = upload_result["segments_data"]

        # Save parsed segments using use case
        save_result = transcript_upload_use_case.save_transcript_segments(
            session_id=session_id,
            user_id=current_user.id,
            segments_data=segments_data,
        )

        # Create a transcription session ID for compatibility
        transcription_session_id = str(uuid4())

        return {
            "message": "Transcript uploaded successfully",
            "session_id": str(session_id),
            "transcription_session_id": transcription_session_id,
            "segments_count": save_result["segments_count"],
            "duration_seconds": save_result["duration_seconds"],
        }

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File encoding not supported. Please use UTF-8 encoding.",
        )
    except DomainException as e:
        if "No filename provided" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        elif "Invalid file format" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        elif "No valid transcript segments found" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        if "Session not found" in str(e):
            raise HTTPException(status_code=404, detail="Session not found or access denied")
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading transcript: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process transcript: {str(e)}"
        )


def _parse_vtt_content(content: str) -> List[dict]:
    """Parse VTT file content and return segments."""
    segments = []
    lines = content.strip().split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip header and empty lines
        if line == "WEBVTT" or line == "" or line.startswith("NOTE"):
            i += 1
            continue

        # Look for timestamp line
        if "-->" in line:
            # Parse timestamp
            timestamp_match = re.match(
                r"(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})",
                line,
            )
            if timestamp_match:
                start_time = _parse_timestamp(timestamp_match.group(1))
                end_time = _parse_timestamp(timestamp_match.group(2))

                # Get the content (next line)
                i += 1
                if i < len(lines):
                    content_line = lines[i].strip()

                    # Extract speaker and content from VTT format like "<v Speaker>Content"
                    speaker_id = 1
                    content_text = content_line

                    speaker_match = re.match(
                        r"<v\s+([^>]+)>\s*(.*)", content_line
                    )
                    if speaker_match:
                        speaker_name = speaker_match.group(1)
                        content_text = speaker_match.group(2)
                        # Simple speaker ID assignment based on name
                        speaker_id = (
                            2
                            if "客戶" in speaker_name
                            or "Client" in speaker_name
                            else 1
                        )

                    segments.append(
                        {
                            "start_seconds": start_time,
                            "end_seconds": end_time,
                            "content": content_text,
                            "speaker_id": speaker_id,
                        }
                    )

        i += 1

    return segments


def _parse_srt_content(content: str) -> List[dict]:
    """Parse SRT file content and return segments."""
    segments = []

    # Split by double newline to get individual subtitle blocks
    blocks = re.split(r"\n\s*\n", content.strip())

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue

        # Skip sequence number (line 0)
        # Parse timestamp (line 1)
        timestamp_line = lines[1].strip()
        timestamp_match = re.match(
            r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})",
            timestamp_line,
        )

        if timestamp_match:
            start_time = _parse_timestamp(
                timestamp_match.group(1).replace(",", ".")
            )
            end_time = _parse_timestamp(
                timestamp_match.group(2).replace(",", ".")
            )

            # Content (lines 2+)
            content_lines = lines[2:]
            content_text = " ".join(content_lines)

            # Extract speaker info if present
            speaker_id = 1

            # Look for speaker prefix like "教練: " or "Coach: "
            speaker_match = re.match(r"(.*?):\s*(.*)", content_text)
            if speaker_match:
                speaker_name = speaker_match.group(1)
                content_text = speaker_match.group(2)
                speaker_id = (
                    2
                    if "客戶" in speaker_name or "Client" in speaker_name
                    else 1
                )

            segments.append(
                {
                    "start_seconds": start_time,
                    "end_seconds": end_time,
                    "content": content_text,
                    "speaker_id": speaker_id,
                }
            )

    return segments


def _parse_timestamp(timestamp_str: str) -> float:
    """Convert timestamp string to seconds."""
    # Handle format: HH:MM:SS.mmm
    time_parts = timestamp_str.split(":")
    if len(time_parts) != 3:
        raise ValueError(f"Invalid timestamp format: {timestamp_str}")

    hours = int(time_parts[0])
    minutes = int(time_parts[1])
    seconds_str = time_parts[2]

    # Handle seconds with milliseconds
    if "." in seconds_str:
        seconds, milliseconds = seconds_str.split(".")
        total_seconds = (
            hours * 3600
            + minutes * 60
            + int(seconds)
            + int(milliseconds) / 1000
        )
    else:
        total_seconds = hours * 3600 + minutes * 60 + int(seconds_str)

    return total_seconds
