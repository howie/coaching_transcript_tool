"""Speaker Role Management Use Cases following Clean Architecture principles.

This module contains use cases for managing speaker role assignments at both
session level (speaker-based) and segment level (individual segment overrides).
"""

from typing import Dict, List, Optional
from uuid import UUID

from ..models.session import Session, SessionStatus
from ..models.transcript import SessionRole, SegmentRole, SpeakerRole
from ..repositories.ports import SessionRepoPort, SpeakerRoleRepoPort, SegmentRoleRepoPort


class SpeakerRoleAssignmentUseCase:
    """Use case for managing speaker role assignments at session level."""

    def __init__(self, session_repo: SessionRepoPort):
        """Initialize with repository dependencies.

        Args:
            session_repo: Session repository port for session operations
        """
        self.session_repo = session_repo

    def execute(
        self,
        session_id: UUID,
        user_id: UUID,
        speaker_roles: Dict[str, str],  # speaker_id -> role_string
    ) -> Dict[str, any]:
        """Execute speaker role assignment for a session.

        Args:
            session_id: ID of the session to update
            user_id: ID of the user performing the operation (for authorization)
            speaker_roles: Dictionary mapping speaker_id to role string ("coach"/"client")

        Returns:
            Dictionary with operation result and updated roles

        Raises:
            ValueError: If session not found, not authorized, or invalid status/roles
        """
        # Get and validate session
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")

        if session.user_id != user_id:
            raise ValueError("Access denied - session not owned by user")

        # Business rule: Can only update roles for completed sessions
        if session.status != SessionStatus.COMPLETED:
            raise ValueError(
                f"Cannot update speaker roles. Session status: {session.status.value}. "
                f"Roles can only be updated for completed sessions."
            )

        # Validate speaker roles
        session_roles = []
        for speaker_id_str, role_str in speaker_roles.items():
            # Validate speaker ID
            try:
                speaker_id = int(speaker_id_str)
                if speaker_id < 1:
                    raise ValueError(f"Invalid speaker ID: {speaker_id}. Must be positive.")
            except ValueError as e:
                raise ValueError(f"Invalid speaker ID format: {speaker_id_str}") from e

            # Validate and convert role
            if role_str not in ["coach", "client"]:
                raise ValueError(
                    f"Invalid role '{role_str}'. Must be 'coach' or 'client'."
                )

            role = SpeakerRole.COACH if role_str == "coach" else SpeakerRole.CLIENT

            # Create domain model for role assignment
            session_role = SessionRole(
                session_id=session_id,
                speaker_id=speaker_id,
                role=role
            )
            session_role.validate()  # Domain validation
            session_roles.append(session_role)

        # Here we would normally call a speaker role repository to save the assignments
        # For now, we'll return the validated assignments
        # TODO: Implement SpeakerRoleRepoPort and update this logic

        return {
            "message": "Speaker roles updated successfully",
            "session_id": str(session_id),
            "speaker_roles": speaker_roles,
            "assignments_count": len(session_roles)
        }


class SegmentRoleAssignmentUseCase:
    """Use case for managing individual segment role assignments."""

    def __init__(self, session_repo: SessionRepoPort):
        """Initialize with repository dependencies.

        Args:
            session_repo: Session repository port for session operations
        """
        self.session_repo = session_repo

    def execute(
        self,
        session_id: UUID,
        user_id: UUID,
        segment_roles: Dict[str, str],  # segment_id -> role_string
    ) -> Dict[str, any]:
        """Execute segment role assignment for specific segments.

        Args:
            session_id: ID of the session containing the segments
            user_id: ID of the user performing the operation (for authorization)
            segment_roles: Dictionary mapping segment_id to role string ("coach"/"client")

        Returns:
            Dictionary with operation result and updated roles

        Raises:
            ValueError: If session not found, not authorized, or invalid status/roles
        """
        # Get and validate session
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")

        if session.user_id != user_id:
            raise ValueError("Access denied - session not owned by user")

        # Business rule: Can only update segment roles for completed sessions
        if session.status != SessionStatus.COMPLETED:
            raise ValueError(
                f"Cannot update segment roles. Session status: {session.status.value}. "
                f"Segment roles can only be updated for completed sessions."
            )

        # Validate segment roles
        segment_role_assignments = []
        for segment_id_str, role_str in segment_roles.items():
            # Validate segment ID format (should be UUID)
            try:
                segment_id = UUID(segment_id_str)
            except ValueError as e:
                raise ValueError(f"Invalid segment ID format: {segment_id_str}") from e

            # Validate and convert role
            if role_str not in ["coach", "client"]:
                raise ValueError(
                    f"Invalid role '{role_str}'. Must be 'coach' or 'client'."
                )

            role = SpeakerRole.COACH if role_str == "coach" else SpeakerRole.CLIENT

            # Create domain model for segment role assignment
            segment_role = SegmentRole(
                session_id=session_id,
                segment_id=segment_id,
                role=role
            )
            segment_role.validate()  # Domain validation
            segment_role_assignments.append(segment_role)

        # Here we would normally call a segment role repository to save the assignments
        # For now, we'll return the validated assignments
        # TODO: Implement SegmentRoleRepoPort and update this logic

        return {
            "message": "Segment roles updated successfully",
            "session_id": str(session_id),
            "segment_roles": segment_roles,
            "assignments_count": len(segment_role_assignments)
        }


class SpeakerRoleRetrievalUseCase:
    """Use case for retrieving speaker role assignments."""

    def __init__(
        self,
        session_repo: SessionRepoPort,
        speaker_role_repo: SpeakerRoleRepoPort,
        segment_role_repo: SegmentRoleRepoPort,
    ):
        """Initialize with repository dependencies.

        Args:
            session_repo: Session repository port for session operations
            speaker_role_repo: Speaker role repository port for speaker role data
            segment_role_repo: Segment role repository port for segment role data
        """
        self.session_repo = session_repo
        self.speaker_role_repo = speaker_role_repo
        self.segment_role_repo = segment_role_repo

    def get_session_speaker_roles(
        self,
        session_id: UUID,
        user_id: UUID,
    ) -> Dict[int, str]:
        """Get current speaker role assignments for a session.

        Args:
            session_id: ID of the session
            user_id: ID of the user requesting the roles (for authorization)

        Returns:
            Dictionary mapping speaker_id to role string

        Raises:
            ValueError: If session not found or not authorized
        """
        # Get and validate session
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")

        if session.user_id != user_id:
            raise ValueError("Access denied - session not owned by user")

        # Get speaker role assignments from repository
        speaker_roles = self.speaker_role_repo.get_by_session_id(session_id)

        # Convert to dictionary mapping speaker_id to role string
        role_assignments = {}
        for role in speaker_roles:
            role_assignments[role.speaker_id] = role.role.value

        return role_assignments

    def get_segment_roles(
        self,
        session_id: UUID,
        user_id: UUID,
    ) -> Dict[str, str]:
        """Get current segment role assignments for a session.

        Args:
            session_id: ID of the session
            user_id: ID of the user requesting the roles (for authorization)

        Returns:
            Dictionary mapping segment_id to role string

        Raises:
            ValueError: If session not found or not authorized
        """
        # Get and validate session
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise ValueError("Session not found")

        if session.user_id != user_id:
            raise ValueError("Access denied - session not owned by user")

        # Get segment role assignments from repository
        segment_roles = self.segment_role_repo.get_by_session_id(session_id)

        # Convert to dictionary mapping segment_id to role string
        segment_assignments = {}
        for seg_role in segment_roles:
            segment_assignments[str(seg_role.segment_id)] = seg_role.role.value

        return segment_assignments