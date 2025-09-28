"""SQLAlchemy implementation of ClientRepoPort with domain model conversion.

This module provides the concrete implementation of client repository
operations using SQLAlchemy ORM with proper domain ↔ ORM conversion,
following Clean Architecture principles.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ....core.models.client import Client as DomainClient
from ....core.repositories.ports import ClientRepoPort
from ....models.client import Client as ClientModel


class SQLAlchemyClientRepository(ClientRepoPort):
    """SQLAlchemy implementation of the ClientRepoPort interface with domain conversion."""

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session

    def _to_domain(self, orm_client: ClientModel) -> DomainClient:
        """Convert ORM Client to domain Client model."""
        if not orm_client:
            return None

        return DomainClient(
            id=orm_client.id,
            user_id=orm_client.user_id,
            name=orm_client.name,
            email=orm_client.email,
            phone=orm_client.phone,
            memo=orm_client.memo,
            source=orm_client.source,
            client_type=orm_client.client_type,
            issue_types=orm_client.issue_types,
            status=orm_client.status,
            is_anonymized=orm_client.is_anonymized,
            anonymized_at=orm_client.anonymized_at,
            created_at=orm_client.created_at,
            updated_at=orm_client.updated_at,
        )

    def _create_orm_client(self, client: DomainClient) -> ClientModel:
        """Create ORM client from domain client."""
        orm_client = ClientModel(
            id=client.id,
            user_id=client.user_id,
            name=client.name,
            email=client.email,
            phone=client.phone,
            memo=client.memo,
            source=client.source,
            client_type=client.client_type,
            issue_types=client.issue_types,
            status=client.status,
            is_anonymized=client.is_anonymized,
            anonymized_at=client.anonymized_at,
            created_at=client.created_at,
            updated_at=client.updated_at,
        )
        return orm_client

    def get_by_id(self, client_id: UUID) -> Optional[DomainClient]:
        """Get client by ID.

        Args:
            client_id: UUID of the client to retrieve

        Returns:
            Client domain entity or None if not found
        """
        try:
            orm_client = self.session.get(ClientModel, client_id)
            return self._to_domain(orm_client) if orm_client else None
        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Database connection error while retrieving client {client_id}"
            ) from e

    def get_by_coach_id(self, coach_id: UUID) -> List[DomainClient]:
        """Get all clients for a coach.

        Args:
            coach_id: UUID of the coach (user)

        Returns:
            List of Client domain entities for the coach
        """
        try:
            orm_clients = (
                self.session.query(ClientModel)
                .filter(ClientModel.user_id == coach_id)
                .order_by(ClientModel.name)
                .all()
            )
            return [self._to_domain(orm_client) for orm_client in orm_clients]
        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Database error retrieving clients for coach {coach_id}"
            ) from e

    def save(self, client: DomainClient) -> DomainClient:
        """Save or update client entity.

        Args:
            client: Client domain entity to save

        Returns:
            Saved Client domain entity with updated fields
        """
        try:
            if client.id:
                # Update existing client
                orm_client = self.session.get(ClientModel, client.id)
                if orm_client:
                    # Update existing client fields manually
                    orm_client.user_id = client.user_id
                    orm_client.name = client.name
                    orm_client.email = client.email
                    orm_client.phone = client.phone
                    orm_client.memo = client.memo
                    orm_client.source = client.source
                    orm_client.client_type = client.client_type
                    orm_client.issue_types = client.issue_types
                    orm_client.status = client.status
                    orm_client.is_anonymized = client.is_anonymized
                    orm_client.anonymized_at = client.anonymized_at
                    orm_client.updated_at = client.updated_at
                else:
                    # Client ID exists but not found in DB - create new
                    orm_client = self._create_orm_client(client)
                    self.session.add(orm_client)
            else:
                # Create new client
                orm_client = self._create_orm_client(client)
                self.session.add(orm_client)

            self.session.flush()  # Get the ID without committing
            return self._to_domain(orm_client)

        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error saving client {client.name}") from e

    def delete(self, client_id: UUID) -> bool:
        """Delete client by ID.

        Args:
            client_id: UUID of the client to delete

        Returns:
            True if client was deleted, False if not found
        """
        try:
            orm_client = self.session.get(ClientModel, client_id)
            if orm_client:
                self.session.delete(orm_client)
                self.session.flush()
                return True
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error deleting client {client_id}") from e

    def search_clients(
        self, coach_id: UUID, query: str, limit: int = 50
    ) -> List[DomainClient]:
        """Search clients by name or email for a coach.

        Args:
            coach_id: UUID of the coach (user)
            query: Search term for name or email
            limit: Maximum number of results to return

        Returns:
            List of Client domain entities matching the search criteria
        """
        try:
            search_filter = or_(
                ClientModel.name.ilike(f"%{query}%"),
                ClientModel.email.ilike(f"%{query}%"),
            )
            query_filter = and_(ClientModel.user_id == coach_id, search_filter)

            orm_clients = (
                self.session.query(ClientModel)
                .filter(query_filter)
                .order_by(ClientModel.name)
                .limit(limit)
                .all()
            )
            return [self._to_domain(orm_client) for orm_client in orm_clients]
        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Database error searching clients for coach {coach_id}"
            ) from e

    def get_clients_paginated(
        self,
        coach_id: UUID,
        query: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[DomainClient], int]:
        """Get paginated clients for a coach with optional search.

        Args:
            coach_id: UUID of the coach (user)
            query: Optional search term for name or email
            page: Page number (1-based)
            page_size: Number of clients per page

        Returns:
            Tuple of (list of clients, total count)
        """
        try:
            # Build base filter
            base_filter = ClientModel.user_id == coach_id

            # Add search filter if provided
            if query:
                search_filter = or_(
                    ClientModel.name.ilike(f"%{query}%"),
                    ClientModel.email.ilike(f"%{query}%"),
                )
                query_filter = and_(base_filter, search_filter)
            else:
                query_filter = base_filter

            # Get total count
            total = self.session.query(ClientModel).filter(query_filter).count()

            # Get paginated results
            offset = (page - 1) * page_size
            orm_clients = (
                self.session.query(ClientModel)
                .filter(query_filter)
                .order_by(ClientModel.name)
                .offset(offset)
                .limit(page_size)
                .all()
            )

            clients = [self._to_domain(orm_client) for orm_client in orm_clients]
            return clients, total

        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Database error getting paginated clients for coach {coach_id}"
            ) from e

    def get_client_with_ownership_check(
        self, client_id: UUID, coach_id: UUID
    ) -> Optional[DomainClient]:
        """Get client by ID with ownership verification.

        Args:
            client_id: UUID of the client to retrieve
            coach_id: UUID of the coach who should own the client

        Returns:
            Client domain entity or None if not found or not owned by coach
        """
        try:
            orm_client = (
                self.session.query(ClientModel)
                .filter(
                    and_(
                        ClientModel.id == client_id,
                        ClientModel.user_id == coach_id,
                    )
                )
                .first()
            )
            return self._to_domain(orm_client) if orm_client else None
        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Database error retrieving client {client_id} for coach {coach_id}"
            ) from e

    def check_email_exists_for_coach(
        self,
        coach_id: UUID,
        email: str,
        exclude_client_id: Optional[UUID] = None,
    ) -> bool:
        """Check if email exists for a coach's clients.

        Args:
            coach_id: UUID of the coach
            email: Email to check
            exclude_client_id: Optional client ID to exclude from check (for updates)

        Returns:
            True if email exists, False otherwise
        """
        try:
            query = self.session.query(ClientModel).filter(
                and_(
                    ClientModel.user_id == coach_id,
                    func.lower(ClientModel.email) == email.lower(),
                    ClientModel.email.isnot(None),
                )
            )

            if exclude_client_id:
                query = query.filter(ClientModel.id != exclude_client_id)

            return query.first() is not None
        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Database error checking email existence for coach {coach_id}"
            ) from e

    def get_anonymized_count_for_coach(self, coach_id: UUID) -> int:
        """Get count of anonymized clients for a coach.

        Args:
            coach_id: UUID of the coach

        Returns:
            Number of anonymized clients for the coach
        """
        try:
            return (
                self.session.query(ClientModel)
                .filter(
                    and_(
                        ClientModel.user_id == coach_id,
                        ClientModel.is_anonymized.is_(True),
                    )
                )
                .count()
            )
        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Database error getting anonymized count for coach {coach_id}"
            ) from e


# Factory function for dependency injection
def create_client_repository(db_session: Session) -> ClientRepoPort:
    """Factory function to create ClientRepository with database session.

    Args:
        db_session: SQLAlchemy database session

    Returns:
        ClientRepoPort implementation
    """
    return SQLAlchemyClientRepository(db_session)
