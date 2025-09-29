"""Session management use cases for Clean Architecture.

This module contains business logic for session creation, management, and transcription
operations. All external dependencies are injected through repository ports.
"""

from __future__ import annotations

import logging
import re
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from ...exceptions import DomainException
from ..config import settings
from ..models.session import Session, SessionStatus
from ..models.transcript import TranscriptSegment
from ..models.usage_log import TranscriptionType, UsageLog
from ..models.user import User
from ..repositories.ports import (
    PlanConfigurationRepoPort,
    SessionRepoPort,
    TranscriptRepoPort,
    UsageLogRepoPort,
    UserRepoPort,
)

logger = logging.getLogger(__name__)


def _replace_session(session: Session, **changes: Any) -> Session:
    """Create an updated Session instance, guarding against bad field names."""
    invalid_fields = set(changes) - session.__dataclass_fields__.keys()
    if invalid_fields:
        invalid_list = ", ".join(sorted(invalid_fields))
        raise ValueError(f"Invalid session fields for replace: {invalid_list}")
    return replace(session, **changes)


def _replace_transcript_segment(
    segment: TranscriptSegment, **changes: Any
) -> TranscriptSegment:
    """Create an updated TranscriptSegment instance with validation."""
    invalid_fields = set(changes) - segment.__dataclass_fields__.keys()
    if invalid_fields:
        invalid_list = ", ".join(sorted(invalid_fields))
        raise ValueError(f"Invalid transcript segment fields: {invalid_list}")

    updated_segment = deepcopy(segment)
    for field_name, value in changes.items():
        setattr(updated_segment, field_name, value)

    immutable_changes = set(changes) - {"content", "updated_at"}
    if immutable_changes:
        updated_segment.validate()
    return updated_segment


class SessionCreationUseCase:
    """Use case for creating new transcription sessions."""

    def __init__(
        self,
        session_repo: SessionRepoPort,
        user_repo: UserRepoPort,
        plan_config_repo: PlanConfigurationRepoPort,
    ):
        self.session_repo = session_repo
        self.user_repo = user_repo
        self.plan_config_repo = plan_config_repo

    def execute(
        self,
        user_id: UUID,
        title: str,
        language: str = "cmn-Hant-TW",
        stt_provider: str = "auto",
    ) -> Session:
        """Create a new transcription session.

        Args:
            user_id: ID of the user creating the session
            title: Session title
            language: Language code for transcription
            stt_provider: STT provider to use

        Returns:
            Created session domain model

        Raises:
            ValueError: If user not found
            DomainException: If user has exceeded plan limits
        """
        # Validate user exists
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")

        # Check plan limits
        self._validate_plan_limits(user)

        # Determine which STT provider should be used for this session
        requested_provider = (stt_provider or "").strip().lower()
        default_provider = settings.STT_PROVIDER

        if requested_provider and requested_provider != "auto":
            provider_to_use = requested_provider
        else:
            provider_to_use = default_provider

        # Create session domain model
        session = Session(
            id=uuid4(),
            user_id=user_id,
            title=title,
            language=language,
            stt_provider=provider_to_use,
            status=SessionStatus.UPLOADING,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        return self.session_repo.save(session)

    def _validate_plan_limits(self, user: User) -> None:
        """Validate user hasn't exceeded plan limits."""
        plan_config = self.plan_config_repo.get_by_plan_type(user.plan)
        if not plan_config:
            # Allow if no plan config found (fallback behavior)
            return

        limits = plan_config.limits
        max_sessions = limits.max_sessions if limits else -1
        max_minutes = limits.max_total_minutes if limits else -1

        # Use current billing period for all limits (avoids counting historical
        # usage)
        billing_period_start = user.current_month_start

        # Check session count limit
        if max_sessions > 0:
            current_session_count = self.session_repo.count_user_sessions(
                user.id, since=billing_period_start
            )
            if current_session_count >= max_sessions:
                raise DomainException(f"Session limit exceeded: {max_sessions}")

        # Check total minutes limit
        if max_minutes > 0:
            current_total_minutes = self.session_repo.get_total_duration_minutes(
                user.id, since=billing_period_start
            )
            if current_total_minutes >= max_minutes:
                raise DomainException(f"Total minutes limit exceeded: {max_minutes}")


class SessionRetrievalUseCase:
    """Use case for retrieving session information."""

    def __init__(
        self,
        session_repo: SessionRepoPort,
        user_repo: UserRepoPort,
        transcript_repo: TranscriptRepoPort,
    ):
        self.session_repo = session_repo
        self.user_repo = user_repo
        self.transcript_repo = transcript_repo

    def get_session_by_id(self, session_id: UUID, user_id: UUID) -> Optional[Session]:
        """Get session by ID, ensuring user owns the session.

        Args:
            session_id: Session ID to retrieve
            user_id: User ID for ownership validation

        Returns:
            Session domain model if found and owned by user, None otherwise
        """
        session = self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            return None
        return session

    def get_user_sessions(
        self,
        user_id: UUID,
        status: Optional[SessionStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Session]:
        """Get sessions for a user with optional filtering.

        Args:
            user_id: User ID
            status: Optional status filter
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            List of session domain models
        """
        return self.session_repo.get_by_user_id(user_id, status, limit, offset)

    def get_session_with_transcript(
        self, session_id: UUID, user_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get session with its transcript segments.

        Args:
            session_id: Session ID
            user_id: User ID for ownership validation

        Returns:
            Dictionary with session and transcript data, None if not found
        """
        session = self.get_session_by_id(session_id, user_id)
        if not session:
            return None

        transcript_segments = self.transcript_repo.get_by_session_id(session_id)

        return {
            "session": session,
            "transcript_segments": transcript_segments,
            "segments_count": len(transcript_segments),
        }


class SessionStatusUpdateUseCase:
    """Use case for updating session status and related operations."""

    def __init__(
        self,
        session_repo: SessionRepoPort,
        user_repo: UserRepoPort,
        usage_log_repo: UsageLogRepoPort,
    ):
        self.session_repo = session_repo
        self.user_repo = user_repo
        self.usage_log_repo = usage_log_repo

    def update_session_status(
        self, session_id: UUID, status: SessionStatus, user_id: UUID
    ) -> Session:
        """Update session status with validation.

        Args:
            session_id: Session ID to update
            status: New status
            user_id: User ID for ownership validation

        Returns:
            Updated session domain model

        Raises:
            ValueError: If session not found or not owned by user
            DomainException: If status transition is invalid
        """
        session = self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Session not found or access denied")

        # Validate status transition
        self._validate_status_transition(session.status, status)

        # Update session
        updated_session = self.session_repo.update_status(session_id, status)

        # Create usage log if status indicates completion
        if status == SessionStatus.COMPLETED:
            self._create_completion_usage_log(updated_session)

        return updated_session

    def _validate_status_transition(
        self, current_status: SessionStatus, new_status: SessionStatus
    ) -> None:
        """Validate if status transition is allowed."""
        valid_transitions = {
            SessionStatus.UPLOADING: [
                SessionStatus.PENDING,
                SessionStatus.FAILED,
            ],
            SessionStatus.PENDING: [
                SessionStatus.PROCESSING,
                SessionStatus.FAILED,
            ],
            SessionStatus.PROCESSING: [
                SessionStatus.COMPLETED,
                SessionStatus.FAILED,
            ],
            SessionStatus.COMPLETED: [SessionStatus.PROCESSING],  # Allow reprocessing
            SessionStatus.FAILED: [
                SessionStatus.PROCESSING,
                SessionStatus.UPLOADING,
            ],
            SessionStatus.CANCELLED: [SessionStatus.UPLOADING],  # Allow restart
        }

        if new_status not in valid_transitions.get(current_status, []):
            raise DomainException(
                f"Invalid status transition from {current_status} to {new_status}"
            )

    def _create_completion_usage_log(self, session: Session) -> None:
        """Create usage log entry when session completes."""
        # Calculate duration in minutes from seconds
        duration_minutes = 0
        if session.duration_seconds and session.duration_seconds > 0:
            duration_minutes = int(session.duration_seconds / 60)

        if duration_minutes <= 0:
            return  # No usage to log

        # Use reasonable default cost calculation (could be enhanced later)
        cost_cents = duration_minutes * 10  # 10 cents per minute as default

        default_provider = settings.STT_PROVIDER
        usage_log = UsageLog(
            id=uuid4(),
            user_id=session.user_id,
            session_id=session.id,
            transcription_type=TranscriptionType.ORIGINAL,
            duration_minutes=duration_minutes,
            cost_cents=cost_cents,
            currency="TWD",
            stt_provider=session.stt_provider or default_provider,
            billable=True,
            created_at=datetime.now(UTC),
        )

        self.usage_log_repo.save(usage_log)


class SessionTranscriptUpdateUseCase:
    """Use case for updating session transcript and speaker roles."""

    def __init__(
        self,
        session_repo: SessionRepoPort,
        transcript_repo: TranscriptRepoPort,
    ):
        self.session_repo = session_repo
        self.transcript_repo = transcript_repo

    def update_speaker_roles(
        self,
        session_id: UUID,
        role_mappings: Dict[str, str],
        user_id: UUID,
    ) -> List[TranscriptSegment]:
        """Update speaker roles for session transcript.

        Args:
            session_id: Session ID
            role_mappings: Dictionary mapping speaker names to roles
            user_id: User ID for ownership validation

        Returns:
            Updated transcript segments

        Raises:
            ValueError: If session not found or not owned by user
        """
        # Validate session ownership
        session = self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Session not found or access denied")

        # Update speaker roles
        updated_segments = self.transcript_repo.update_speaker_roles(
            session_id, role_mappings
        )

        # Update session metadata if needed
        updated_session = _replace_session(session, updated_at=datetime.now(UTC))
        self.session_repo.save(updated_session)

        return updated_segments

    def update_session_metadata(
        self,
        session_id: UUID,
        metadata: Dict[str, Any],
        user_id: UUID,
    ) -> Session:
        """Update session metadata.

        Args:
            session_id: Session ID
            metadata: Metadata to update
            user_id: User ID for ownership validation

        Returns:
            Updated session domain model

        Raises:
            ValueError: If session not found or not owned by user
        """
        session = self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Session not found or access denied")

        # Create updated session domain model with new metadata
        updated_fields = {}

        if "duration_seconds" in metadata:
            updated_fields["duration_seconds"] = metadata["duration_seconds"]

        if "audio_filename" in metadata:
            updated_fields["audio_filename"] = metadata["audio_filename"]

        if "error_message" in metadata:
            updated_fields["error_message"] = metadata["error_message"]

        updated_fields["updated_at"] = datetime.now(UTC)

        # Create new session instance with updated fields
        updated_session = _replace_session(session, **updated_fields)
        return self.session_repo.save(updated_session)

    def update_segment_content(
        self,
        session_id: UUID,
        user_id: UUID,
        segment_content: Dict[str, str],
    ) -> List[TranscriptSegment]:
        """Update transcript segment content for a completed session."""
        if not segment_content:
            raise ValueError("No segment content provided")

        session = self.session_repo.get_by_id(session_id)
        if session is None:
            raise ValueError("Session not found")

        if session.user_id != user_id:
            raise ValueError("Access denied")

        if session.status != SessionStatus.COMPLETED:
            raise ValueError(
                f"Cannot update segment content. Session status: {session.status.value}. Content can only be updated for completed sessions."
            )

        normalized_updates: Dict[UUID, str] = {}
        for segment_id_str, new_content in segment_content.items():
            if new_content is None:
                raise ValueError(
                    f"Segment content cannot be empty for {segment_id_str}"
                )

            try:
                segment_uuid = UUID(segment_id_str)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid segment ID format: {segment_id_str}"
                ) from exc

            normalized_updates[segment_uuid] = new_content

        existing_segments = self.transcript_repo.get_by_session_id(session_id)
        segments_by_id = {
            segment.id: segment
            for segment in existing_segments
            if segment.id is not None
        }

        missing_segments = [
            str(segment_id)
            for segment_id in normalized_updates
            if segment_id not in segments_by_id
        ]
        if missing_segments:
            missing_list = ", ".join(missing_segments)
            raise ValueError(f"Segment not found: {missing_list}")

        updated_segments = [
            _replace_transcript_segment(
                segments_by_id[segment_id],
                content=new_content,
                updated_at=datetime.now(UTC),
            )
            for segment_id, new_content in normalized_updates.items()
        ]

        persisted_segments = self.transcript_repo.update_segment_content(
            session_id, updated_segments
        )

        updated_session = _replace_session(session, updated_at=datetime.now(UTC))
        self.session_repo.save(updated_session)

        return persisted_segments


class SessionUploadManagementUseCase:
    """Use case for managing audio file uploads (URL generation and confirmation)."""

    def __init__(
        self,
        session_repo: SessionRepoPort,
        user_repo: UserRepoPort,
        plan_config_repo: PlanConfigurationRepoPort,
    ):
        self.session_repo = session_repo
        self.user_repo = user_repo
        self.plan_config_repo = plan_config_repo

    def generate_upload_url(
        self,
        session_id: UUID,
        user_id: UUID,
        filename: str,
        file_size_mb: float,
    ) -> Dict[str, Any]:
        """Generate signed upload URL for audio file.

        Args:
            session_id: Session ID
            user_id: User ID for ownership validation
            filename: Original filename
            file_size_mb: File size in MB for validation

        Returns:
            Dictionary with upload URL, GCS path, and expiration

        Raises:
            ValueError: If session not found or not owned by user
            DomainException: If file size exceeds plan limits or session status invalid
        """
        # Validate user and get plan limits
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")

        plan_config = self.plan_config_repo.get_by_plan_type(user.plan)
        if plan_config and plan_config.limits:
            max_file_size = plan_config.limits.max_file_size_mb
            if file_size_mb > max_file_size:
                raise DomainException(
                    f"File size {file_size_mb:.1f}MB exceeds plan limit of {max_file_size}MB"
                )

        # Validate session ownership and status
        session = self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Session not found or access denied")

        if session.status not in [
            SessionStatus.UPLOADING,
            SessionStatus.FAILED,
        ]:
            raise DomainException(
                f"Cannot upload to session with status {session.status.value}. "
                f"Upload is only allowed for sessions in UPLOADING or FAILED status."
            )

        # Reset failed session to uploading state
        if session.status == SessionStatus.FAILED:
            session = _replace_session(
                session,
                status=SessionStatus.UPLOADING,
                error_message=None,
                audio_filename=None,
                gcs_audio_path=None,
                transcription_job_id=None,
            )
            session = self.session_repo.save(session)

        return {
            "session": session,
            "filename": filename,
            "file_size_mb": file_size_mb,
            "user_plan": user.plan,
        }

    def confirm_upload(
        self,
        session_id: UUID,
        user_id: UUID,
    ) -> Dict[str, Any]:
        """Confirm that audio file was successfully uploaded.

        Args:
            session_id: Session ID
            user_id: User ID for ownership validation

        Returns:
            Dictionary with confirmation status and file info

        Raises:
            ValueError: If session not found or not owned by user
        """
        # Validate session ownership
        session = self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Session not found or access denied")

        return {
            "session": session,
            "gcs_path": session.gcs_audio_path,
        }

    def update_session_file_info(
        self,
        session_id: UUID,
        user_id: UUID,
        audio_filename: str,
        gcs_audio_path: str,
    ) -> Session:
        """Update session with file information after URL generation.

        Args:
            session_id: Session ID
            user_id: User ID for ownership validation
            audio_filename: Original filename
            gcs_audio_path: GCS storage path

        Returns:
            Updated session domain model

        Raises:
            ValueError: If session not found or not owned by user
        """
        session = self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Session not found or access denied")

        updated_session = _replace_session(
            session,
            audio_filename=audio_filename,
            gcs_audio_path=gcs_audio_path,
            updated_at=datetime.now(UTC),
        )

        return self.session_repo.save(updated_session)

    def mark_upload_complete(
        self,
        session_id: UUID,
        user_id: UUID,
    ) -> Session:
        """Mark upload as complete and update session status.

        Args:
            session_id: Session ID
            user_id: User ID for ownership validation

        Returns:
            Updated session model

        Raises:
            ValueError: If session not found or not owned by user
        """
        session = self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Session not found or access denied")

        if session.status == SessionStatus.UPLOADING:
            session = _replace_session(
                session,
                status=SessionStatus.PENDING,
                updated_at=datetime.now(UTC),
            )
            session = self.session_repo.save(session)

        return session


class SessionTranscriptionManagementUseCase:
    """Use case for managing transcription operations (start, retry)."""

    def __init__(
        self,
        session_repo: SessionRepoPort,
        transcript_repo: TranscriptRepoPort,
    ):
        self.session_repo = session_repo
        self.transcript_repo = transcript_repo

    def start_transcription(
        self,
        session_id: UUID,
        user_id: UUID,
    ) -> Dict[str, Any]:
        """Start transcription processing for uploaded audio.

        Args:
            session_id: Session ID
            user_id: User ID for ownership validation

        Returns:
            Dictionary with transcription info for task queue

        Raises:
            ValueError: If session not found or not owned by user
            DomainException: If session status or file invalid
        """
        # Validate session ownership
        session = self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Session not found or access denied")

        # Validate session status
        if session.status not in [
            SessionStatus.UPLOADING,
            SessionStatus.PENDING,
        ]:
            raise DomainException(
                f"Cannot start transcription for session with status {session.status.value}"
            )

        if not session.gcs_audio_path:
            raise DomainException("No audio file uploaded")

        # Update status to processing
        session = replace(
            session,
            status=SessionStatus.PROCESSING,
            updated_at=datetime.now(UTC),
        )
        session = self.session_repo.save(session)

        return {
            "session_id": str(session_id),
            "gcs_uri": session.gcs_audio_path,
            "language": session.language,
            "original_filename": session.audio_filename,
            "stt_provider": session.stt_provider,
        }

    def retry_transcription(
        self,
        session_id: UUID,
        user_id: UUID,
    ) -> Dict[str, Any]:
        """Retry transcription for failed sessions.

        Args:
            session_id: Session ID
            user_id: User ID for ownership validation

        Returns:
            Dictionary with transcription info for task queue

        Raises:
            ValueError: If session not found or not owned by user
            DomainException: If session status invalid or file missing
        """
        # Validate session ownership
        session = self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Session not found or access denied")

        # Only allow retry for FAILED sessions
        if session.status != SessionStatus.FAILED:
            raise DomainException(
                f"Cannot retry transcription for session with status {session.status.value}. "
                f"Only failed sessions can be retried."
            )

        if not session.gcs_audio_path:
            raise DomainException("No audio file found. Please re-upload the file.")

        # Clear existing data and reset status
        session = replace(
            session,
            status=SessionStatus.PROCESSING,
            error_message=None,
            transcription_job_id=None,
            updated_at=datetime.now(UTC),
        )

        # Clear existing transcript segments and processing status
        self.transcript_repo.delete_by_session_id(session_id)

        session = self.session_repo.save(session)

        return {
            "session_id": str(session_id),
            "gcs_uri": session.gcs_audio_path,
            "language": session.language,
            "original_filename": session.audio_filename,
            "stt_provider": session.stt_provider,
            "retry": True,
        }

    def update_transcription_job_id(
        self,
        session_id: UUID,
        user_id: UUID,
        job_id: str,
    ) -> Session:
        """Update session with transcription job ID.

        Args:
            session_id: Session ID
            user_id: User ID for ownership validation
            job_id: Celery task ID

        Returns:
            Updated session model

        Raises:
            ValueError: If session not found or not owned by user
        """
        session = self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Session not found or access denied")

        session = replace(
            session, transcription_job_id=job_id, updated_at=datetime.now(UTC)
        )

        return self.session_repo.save(session)


class SessionExportUseCase:
    """Use case for exporting session transcripts in various formats."""

    def __init__(
        self,
        session_repo: SessionRepoPort,
        transcript_repo: TranscriptRepoPort,
    ):
        self.session_repo = session_repo
        self.transcript_repo = transcript_repo

    def export_transcript(
        self,
        session_id: UUID,
        user_id: UUID,
        format: str = "json",
    ) -> Dict[str, Any]:
        """Export transcript in specified format.

        Args:
            session_id: Session ID
            user_id: User ID for ownership validation
            format: Export format (json, vtt, srt, txt, xlsx)

        Returns:
            Dictionary with session, segments, and format info

        Raises:
            ValueError: If session not found or not owned by user
            DomainException: If transcript not available or format invalid
        """
        # Validate session ownership
        session = self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Session not found or access denied")

        if session.status != SessionStatus.COMPLETED:
            raise DomainException(
                f"Transcript not available. Session status: {session.status.value}"
            )

        # Get transcript segments
        segments = self.transcript_repo.get_by_session_id(session_id)
        if not segments:
            raise DomainException("No transcript segments found")

        # Validate format
        valid_formats = ["json", "vtt", "srt", "txt", "xlsx"]
        if format not in valid_formats:
            raise DomainException(
                f"Invalid format. Supported: {', '.join(valid_formats)}"
            )

        return {
            "session": session,
            "segments": segments,
            "format": format,
        }


class SessionStatusRetrievalUseCase:
    """Use case for retrieving detailed session processing status."""

    def __init__(
        self,
        session_repo: SessionRepoPort,
    ):
        self.session_repo = session_repo

    def get_detailed_status(
        self,
        session_id: UUID,
        user_id: UUID,
    ) -> Dict[str, Any]:
        """Get detailed processing status for a session.

        Args:
            session_id: Session ID
            user_id: User ID for ownership validation

        Returns:
            Dictionary with detailed status information including processing status

        Raises:
            ValueError: If session not found or not owned by user
        """
        # Validate session ownership
        session = self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Session not found or access denied")

        # Create processing status info based on session status
        processing_status = self._create_processing_status(session)

        return {
            "session": session,
            "processing_status": processing_status,
        }

    def _create_processing_status(self, session: Session) -> Dict[str, Any]:
        """Create processing status based on session status.

        Args:
            session: Session domain model

        Returns:
            Dictionary with processing status information
        """
        # Map session status to processing status information
        status_map = {
            SessionStatus.UPLOADING: {
                "progress_percentage": 0,
                "message": "Waiting for file upload",
                "started_at": None,
                "estimated_completion": None,
                "processing_speed": None,
                "duration_processed": None,
                "duration_total": session.duration_seconds,
            },
            SessionStatus.PENDING: {
                "progress_percentage": 5,
                "message": "File uploaded, queued for processing",
                "started_at": None,
                "estimated_completion": None,
                "processing_speed": None,
                "duration_processed": None,
                "duration_total": session.duration_seconds,
            },
            SessionStatus.PROCESSING: {
                "progress_percentage": self._calculate_processing_progress(session),
                "message": self._get_processing_message(session),
                "started_at": (session.transcription_started_at or session.updated_at),
                "estimated_completion": self._estimate_completion_time(session),
                "processing_speed": self._calculate_processing_speed(session),
                "duration_processed": self._get_duration_processed(session),
                "duration_total": session.duration_seconds,
            },
            SessionStatus.COMPLETED: {
                "progress_percentage": 100,
                "message": "Transcription complete!",
                "started_at": (session.transcription_started_at or session.updated_at),
                "estimated_completion": (
                    session.transcription_completed_at or session.updated_at
                ),
                "processing_speed": None,
                "duration_processed": session.duration_seconds,
                "duration_total": session.duration_seconds,
            },
            SessionStatus.FAILED: {
                "progress_percentage": 0,
                "message": session.error_message or "Processing failed",
                "started_at": session.transcription_started_at,
                "estimated_completion": None,
                "processing_speed": None,
                "duration_processed": None,
                "duration_total": session.duration_seconds,
            },
            SessionStatus.CANCELLED: {
                "progress_percentage": 0,
                "message": "Processing cancelled",
                "started_at": None,
                "estimated_completion": None,
                "processing_speed": None,
                "duration_processed": None,
                "duration_total": session.duration_seconds,
            },
        }

        return status_map.get(
            session.status,
            {
                "progress_percentage": 0,
                "message": "Unknown status",
                "started_at": None,
                "estimated_completion": None,
                "processing_speed": None,
                "duration_processed": None,
                "duration_total": session.duration_seconds,
            },
        )

    def _calculate_processing_progress(self, session: Session) -> int:
        """Calculate processing progress percentage for processing sessions."""
        if session.status != SessionStatus.PROCESSING:
            return 0

        # If we have actual progress from session, use it
        if hasattr(session, "progress_percentage") and session.progress_percentage > 0:
            return min(95, session.progress_percentage)  # Cap at 95% until complete

        # Time-based progress estimate
        if session.transcription_started_at and session.duration_seconds:
            elapsed = (
                datetime.now(UTC) - session.transcription_started_at
            ).total_seconds()
            # Assume 4x real-time processing speed
            expected_total = session.duration_seconds * 4
            if expected_total > 0:
                progress = min(95, int((elapsed / expected_total) * 100))
                return max(10, progress)  # Always show at least 10% if processing

        return 10  # Default progress for processing sessions

    def _get_processing_message(self, session: Session) -> str:
        """Get appropriate processing message based on progress."""
        progress = self._calculate_processing_progress(session)

        if progress < 25:
            return "Starting audio processing..."
        elif progress < 50:
            return "Processing audio segments..."
        elif progress < 75:
            return "Analyzing speech patterns..."
        elif progress < 95:
            return "Finalizing transcription..."
        else:
            return "Almost done..."

    def _estimate_completion_time(self, session: Session) -> Optional[datetime]:
        """Estimate completion time for processing sessions."""
        if session.status != SessionStatus.PROCESSING or not session.duration_seconds:
            return None

        if session.transcription_started_at:
            elapsed = (
                datetime.now(UTC) - session.transcription_started_at
            ).total_seconds()
            # Assume 4x real-time processing
            estimated_total = session.duration_seconds * 4
            remaining = max(
                60, estimated_total - elapsed
            )  # At least 1 minute remaining
            return datetime.now(UTC) + timedelta(seconds=remaining)
        else:
            # No start time, estimate 2 hours max
            return datetime.now(UTC) + timedelta(hours=2)

    def _calculate_processing_speed(self, session: Session) -> Optional[float]:
        """Calculate processing speed if available."""
        if (
            session.status != SessionStatus.PROCESSING
            or not session.transcription_started_at
            or not session.duration_seconds
        ):
            return None

        elapsed = (datetime.now(UTC) - session.transcription_started_at).total_seconds()
        if elapsed > 0:
            # Rough estimate: assume we've processed proportionally to elapsed
            # time
            progress_ratio = self._calculate_processing_progress(session) / 100.0
            processed_duration = session.duration_seconds * progress_ratio
            if processed_duration > 0:
                return processed_duration / elapsed

        return None

    def _get_duration_processed(self, session: Session) -> Optional[int]:
        """Get duration processed based on progress."""
        if session.status == SessionStatus.COMPLETED:
            return session.duration_seconds
        elif session.status == SessionStatus.PROCESSING and session.duration_seconds:
            progress_ratio = self._calculate_processing_progress(session) / 100.0
            return int(session.duration_seconds * progress_ratio)

        return None


class SessionTranscriptUploadUseCase:
    """Use case for uploading transcript files (VTT/SRT) directly to sessions."""

    def __init__(
        self,
        session_repo: SessionRepoPort,
        transcript_repo: TranscriptRepoPort,
    ):
        self.session_repo = session_repo
        self.transcript_repo = transcript_repo

    def upload_transcript_file(
        self,
        session_id: UUID,
        user_id: UUID,
        filename: str,
        content: str,
    ) -> Dict[str, Any]:
        """Upload and process transcript file content.

        Args:
            session_id: Session ID
            user_id: User ID for ownership validation
            filename: Original filename
            content: File content as string

        Returns:
            Dictionary with upload results

        Raises:
            ValueError: If session not found or not owned by user
            DomainException: If file format invalid or parsing fails
        """
        # Validate session ownership
        session = self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Session not found or access denied")

        # Validate file format
        if not filename:
            raise DomainException("No filename provided")

        file_extension = filename.split(".")[-1].lower()
        if file_extension not in ["vtt", "srt"]:
            raise DomainException(
                "Invalid file format. Only VTT and SRT files are supported."
            )

        # Parse the transcript content
        segments = []
        if file_extension == "vtt":
            segments = self._parse_vtt_content(content)
        elif file_extension == "srt":
            segments = self._parse_srt_content(content)

        if not segments:
            raise DomainException("No valid transcript segments found in file")

        return {
            "session": session,
            "segments_data": segments,
            "file_extension": file_extension,
        }

    def save_transcript_segments(
        self,
        session_id: UUID,
        user_id: UUID,
        segments_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Save parsed transcript segments to database.

        Args:
            session_id: Session ID
            user_id: User ID for ownership validation
            segments_data: List of segment dictionaries

        Returns:
            Dictionary with save results

        Raises:
            ValueError: If session not found or not owned by user
        """
        # Validate session ownership
        session = self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Session not found or access denied")

        # Create transcript segments
        segments = []
        total_duration = 0

        for segment_data in segments_data:
            segment = TranscriptSegment(
                id=uuid4(),
                session_id=session_id,
                speaker_id=segment_data.get("speaker_id", 1),
                start_seconds=segment_data["start_seconds"],
                end_seconds=segment_data["end_seconds"],
                content=segment_data["content"],
                confidence=1.0,  # Manual upload, assume high confidence
            )
            total_duration = max(total_duration, segment_data["end_seconds"])
            segments.append(segment)

        # Save segments
        saved_segments = self.transcript_repo.save_segments(segments)

        # Update session with transcript info
        session = replace(
            session,
            duration_seconds=total_duration,
            status=SessionStatus.COMPLETED,
            updated_at=datetime.now(UTC),
        )
        session = self.session_repo.save(session)

        return {
            "session": session,
            "segments_count": len(saved_segments),
            "duration_seconds": total_duration,
        }

    def _parse_vtt_content(self, content: str) -> List[Dict[str, Any]]:
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
                    start_time = self._parse_timestamp(timestamp_match.group(1))
                    end_time = self._parse_timestamp(timestamp_match.group(2))

                    # Get the content (next line)
                    i += 1
                    if i < len(lines):
                        content_line = lines[i].strip()

                        # Extract speaker and content from VTT format like "<v
                        # Speaker>Content"
                        speaker_id = 1
                        content_text = content_line

                        speaker_match = re.match(r"<v\s+([^>]+)>\s*(.*)", content_line)
                        if speaker_match:
                            speaker_name = speaker_match.group(1)
                            content_text = speaker_match.group(2)
                            # Simple speaker ID assignment based on name
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

            i += 1

        return segments

    def _parse_srt_content(self, content: str) -> List[Dict[str, Any]]:
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
                start_time = self._parse_timestamp(
                    timestamp_match.group(1).replace(",", ".")
                )
                end_time = self._parse_timestamp(
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
                        2 if "客戶" in speaker_name or "Client" in speaker_name else 1
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

    def _parse_timestamp(self, timestamp_str: str) -> float:
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
                hours * 3600 + minutes * 60 + int(seconds) + int(milliseconds) / 1000
            )
        else:
            total_seconds = hours * 3600 + minutes * 60 + int(seconds_str)

        return total_seconds
