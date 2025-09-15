"""Session management use cases for Clean Architecture.

This module contains business logic for session creation, management, and transcription
operations. All external dependencies are injected through repository ports.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal

from ..repositories.ports import (
    SessionRepoPort,
    UserRepoPort,
    UsageLogRepoPort,
    TranscriptRepoPort,
    PlanConfigurationRepoPort,
)
from ...models.session import Session as SessionModel, SessionStatus
from ...models.user import User, UserPlan
from ...models.usage_log import UsageLog, TranscriptionType
from ...models.transcript import TranscriptSegment
from ...exceptions import DomainException


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
    ) -> SessionModel:
        """Create a new transcription session.
        
        Args:
            user_id: ID of the user creating the session
            title: Session title
            language: Language code for transcription
            stt_provider: STT provider to use
            
        Returns:
            Created session model
            
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

        # Create session
        session = SessionModel(
            id=uuid4(),
            user_id=user_id,
            title=title,
            language=language,
            stt_provider=stt_provider if stt_provider != "auto" else None,
            status=SessionStatus.CREATED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        return self.session_repo.save(session)

    def _validate_plan_limits(self, user: User) -> None:
        """Validate user hasn't exceeded plan limits."""
        plan_config = self.plan_config_repo.get_by_plan_type(user.plan)
        if not plan_config:
            # Allow if no plan config found (fallback behavior)
            return

        limits = plan_config.limits
        max_sessions = limits.get("maxSessions", -1)
        max_minutes = limits.get("maxMinutes", -1)

        # Check session count limit
        if max_sessions > 0:
            current_session_count = self.session_repo.count_user_sessions(user.id)
            if current_session_count >= max_sessions:
                raise DomainException(f"Session limit exceeded: {max_sessions}")

        # Check total minutes limit
        if max_minutes > 0:
            current_total_minutes = self.session_repo.get_total_duration_minutes(user.id)
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

    def get_session_by_id(self, session_id: UUID, user_id: UUID) -> Optional[SessionModel]:
        """Get session by ID, ensuring user owns the session.
        
        Args:
            session_id: Session ID to retrieve
            user_id: User ID for ownership validation
            
        Returns:
            Session model if found and owned by user, None otherwise
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
    ) -> List[SessionModel]:
        """Get sessions for a user with optional filtering.
        
        Args:
            user_id: User ID
            status: Optional status filter
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            
        Returns:
            List of session models
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
    ) -> SessionModel:
        """Update session status with validation.
        
        Args:
            session_id: Session ID to update
            status: New status
            user_id: User ID for ownership validation
            
        Returns:
            Updated session model
            
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
            SessionStatus.CREATED: [SessionStatus.UPLOADED, SessionStatus.FAILED],
            SessionStatus.UPLOADED: [SessionStatus.PROCESSING, SessionStatus.FAILED],
            SessionStatus.PROCESSING: [SessionStatus.COMPLETED, SessionStatus.FAILED],
            SessionStatus.COMPLETED: [SessionStatus.PROCESSING],  # Allow reprocessing
            SessionStatus.FAILED: [SessionStatus.PROCESSING, SessionStatus.UPLOADED],
        }

        if new_status not in valid_transitions.get(current_status, []):
            raise DomainException(
                f"Invalid status transition from {current_status} to {new_status}"
            )

    def _create_completion_usage_log(self, session: SessionModel) -> None:
        """Create usage log entry when session completes."""
        if not session.duration_minutes or session.duration_minutes <= 0:
            return  # No usage to log

        cost = Decimal(session.stt_cost_usd or "0.00")
        
        usage_log = UsageLog(
            id=uuid4(),
            user_id=session.user_id,
            session_id=session.id,
            transcription_type=TranscriptionType.AUDIO,
            duration_minutes=session.duration_minutes,
            cost_usd=cost,
            stt_provider=session.stt_provider,
            language=session.language,
            created_at=datetime.utcnow(),
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
        session.updated_at = datetime.utcnow()
        self.session_repo.save(session)

        return updated_segments

    def update_session_metadata(
        self,
        session_id: UUID,
        metadata: Dict[str, Any],
        user_id: UUID,
    ) -> SessionModel:
        """Update session metadata.
        
        Args:
            session_id: Session ID
            metadata: Metadata to update
            user_id: User ID for ownership validation
            
        Returns:
            Updated session model
            
        Raises:
            ValueError: If session not found or not owned by user
        """
        session = self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Session not found or access denied")

        # Update allowed metadata fields
        if "duration_seconds" in metadata:
            session.duration_seconds = metadata["duration_seconds"]
            session.duration_minutes = metadata["duration_seconds"] / 60.0

        if "audio_filename" in metadata:
            session.audio_filename = metadata["audio_filename"]

        if "stt_cost_usd" in metadata:
            session.stt_cost_usd = str(metadata["stt_cost_usd"])

        if "provider_metadata" in metadata:
            session.provider_metadata = metadata["provider_metadata"]

        if "error_message" in metadata:
            session.error_message = metadata["error_message"]

        session.updated_at = datetime.utcnow()
        return self.session_repo.save(session)