"""SQLAlchemy implementation of speaker role repository ports.

This module provides concrete implementations for speaker and segment role repository
operations using SQLAlchemy ORM with proper domain ↔ ORM conversion.
"""

from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ....core.repositories.ports import SpeakerRoleRepoPort, SegmentRoleRepoPort
from ....core.models.transcript import SessionRole, SegmentRole
from ....models.transcript import SessionRole as SessionRoleModel, SegmentRole as SegmentRoleModel


class SQLAlchemySpeakerRoleRepository(SpeakerRoleRepoPort):
    """SQLAlchemy implementation of the SpeakerRoleRepoPort interface."""

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session

    def get_by_session_id(self, session_id: UUID) -> List[SessionRole]:
        """Get all speaker role assignments for a session.

        Args:
            session_id: Session ID to retrieve roles for

        Returns:
            List of SessionRole domain entities
        """
        try:
            orm_roles = (
                self.session.query(SessionRoleModel)
                .filter(SessionRoleModel.session_id == session_id)
                .all()
            )
            return [self._to_domain(orm_role) for orm_role in orm_roles]
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error retrieving speaker roles for session {session_id}") from e

    def save_speaker_roles(
        self, session_id: UUID, speaker_roles: List[SessionRole]
    ) -> List[SessionRole]:
        """Save or update speaker role assignments for a session.

        Args:
            session_id: Session ID
            speaker_roles: List of SessionRole domain entities to save

        Returns:
            List of saved SessionRole domain entities
        """
        try:
            # Delete existing roles for session
            self.delete_by_session_id(session_id)

            # Save new roles
            saved_roles = []
            for role in speaker_roles:
                orm_role = self._from_domain(role)
                self.session.add(orm_role)
                self.session.flush()  # Get ID without committing
                saved_roles.append(self._to_domain(orm_role))

            return saved_roles

        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error saving speaker roles for session {session_id}") from e

    def delete_by_session_id(self, session_id: UUID) -> None:
        """Delete all speaker role assignments for a session.

        Args:
            session_id: Session ID to delete roles for
        """
        try:
            self.session.query(SessionRoleModel).filter(
                SessionRoleModel.session_id == session_id
            ).delete()
            self.session.flush()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error deleting speaker roles for session {session_id}") from e

    def _to_domain(self, orm_role: SessionRoleModel) -> SessionRole:
        """Convert ORM model to domain entity."""
        return SessionRole(
            id=orm_role.id,
            session_id=orm_role.session_id,
            speaker_id=orm_role.speaker_id,
            role=orm_role.role,
            created_at=orm_role.created_at,
            updated_at=orm_role.updated_at,
        )

    def _from_domain(self, domain_role: SessionRole) -> SessionRoleModel:
        """Convert domain entity to ORM model."""
        return SessionRoleModel(
            id=domain_role.id,
            session_id=domain_role.session_id,
            speaker_id=domain_role.speaker_id,
            role=domain_role.role,
            created_at=domain_role.created_at,
            updated_at=domain_role.updated_at,
        )


class SQLAlchemySegmentRoleRepository(SegmentRoleRepoPort):
    """SQLAlchemy implementation of the SegmentRoleRepoPort interface."""

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session

    def get_by_session_id(self, session_id: UUID) -> List[SegmentRole]:
        """Get all segment role assignments for a session.

        Args:
            session_id: Session ID to retrieve roles for

        Returns:
            List of SegmentRole domain entities
        """
        try:
            orm_roles = (
                self.session.query(SegmentRoleModel)
                .filter(SegmentRoleModel.session_id == session_id)
                .all()
            )
            return [self._to_domain(orm_role) for orm_role in orm_roles]
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error retrieving segment roles for session {session_id}") from e

    def save_segment_roles(
        self, session_id: UUID, segment_roles: List[SegmentRole]
    ) -> List[SegmentRole]:
        """Save or update segment role assignments for a session.

        Args:
            session_id: Session ID
            segment_roles: List of SegmentRole domain entities to save

        Returns:
            List of saved SegmentRole domain entities
        """
        try:
            # Delete existing roles for session
            self.delete_by_session_id(session_id)

            # Save new roles
            saved_roles = []
            for role in segment_roles:
                orm_role = self._from_domain(role)
                self.session.add(orm_role)
                self.session.flush()  # Get ID without committing
                saved_roles.append(self._to_domain(orm_role))

            return saved_roles

        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error saving segment roles for session {session_id}") from e

    def delete_by_session_id(self, session_id: UUID) -> None:
        """Delete all segment role assignments for a session.

        Args:
            session_id: Session ID to delete roles for
        """
        try:
            self.session.query(SegmentRoleModel).filter(
                SegmentRoleModel.session_id == session_id
            ).delete()
            self.session.flush()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error deleting segment roles for session {session_id}") from e

    def _to_domain(self, orm_role: SegmentRoleModel) -> SegmentRole:
        """Convert ORM model to domain entity."""
        return SegmentRole(
            id=orm_role.id,
            session_id=orm_role.session_id,
            segment_id=orm_role.segment_id,
            role=orm_role.role,
            created_at=orm_role.created_at,
            updated_at=orm_role.updated_at,
        )

    def _from_domain(self, domain_role: SegmentRole) -> SegmentRoleModel:
        """Convert domain entity to ORM model."""
        return SegmentRoleModel(
            id=domain_role.id,
            session_id=domain_role.session_id,
            segment_id=domain_role.segment_id,
            role=domain_role.role,
            created_at=domain_role.created_at,
            updated_at=domain_role.updated_at,
        )


# Factory functions for dependency injection
def create_speaker_role_repository(db_session: Session) -> SpeakerRoleRepoPort:
    """Factory function to create SpeakerRoleRepository with database session."""
    return SQLAlchemySpeakerRoleRepository(db_session)


def create_segment_role_repository(db_session: Session) -> SegmentRoleRepoPort:
    """Factory function to create SegmentRoleRepository with database session."""
    return SQLAlchemySegmentRoleRepository(db_session)