"""Client management use cases for Clean Architecture.

This module contains the business logic for client management operations,
following the Clean Architecture principles with dependency injection.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from ..models.client import Client
from ..repositories.ports import ClientRepoPort, UserRepoPort


class ClientRetrievalUseCase:
    """Use case for retrieving client information."""

    def __init__(self, client_repo: ClientRepoPort, user_repo: UserRepoPort):
        """Initialize use case with repository dependencies.

        Args:
            client_repo: Client repository implementation
            user_repo: User repository implementation
        """
        self.client_repo = client_repo
        self.user_repo = user_repo

    def get_client_by_id(self, client_id: UUID, coach_id: UUID) -> Optional[Client]:
        """Get a client by ID with ownership verification.

        Args:
            client_id: UUID of the client to retrieve
            coach_id: UUID of the coach requesting the client

        Returns:
            Client domain entity if found and owned by coach, None otherwise
        """
        return self.client_repo.get_client_with_ownership_check(client_id, coach_id)

    def list_clients_paginated(
        self,
        coach_id: UUID,
        query: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Client], int, int]:
        """List clients for a coach with pagination and optional search.

        Args:
            coach_id: UUID of the coach
            query: Optional search term for name or email
            page: Page number (1-based)
            page_size: Number of clients per page

        Returns:
            Tuple of (clients, total_count, total_pages)
        """
        # Verify coach exists
        coach = self.user_repo.get_by_id(coach_id)
        if not coach:
            raise ValueError(f"Coach with ID {coach_id} not found")

        clients, total = self.client_repo.get_clients_paginated(
            coach_id, query, page, page_size
        )

        total_pages = (total + page_size - 1) // page_size
        return clients, total, total_pages

    def get_client_statistics(self, coach_id: UUID) -> Dict[str, List[Dict[str, Any]]]:
        """Get client statistics for charts and analytics.

        Args:
            coach_id: UUID of the coach

        Returns:
            Dictionary with source_distribution, type_distribution, and issue_distribution
        """
        # Verify coach exists
        coach = self.user_repo.get_by_id(coach_id)
        if not coach:
            raise ValueError(f"Coach with ID {coach_id} not found")

        clients = self.client_repo.get_by_coach_id(coach_id)

        # Initialize empty distributions
        source_distribution = []
        type_distribution = []
        issue_distribution = []

        if clients:
            # Translation mappings for display names
            source_labels = {
                "referral": "別人推薦",
                "organic": "自然搜尋",
                "friend": "朋友介紹",
                "social_media": "社群媒體",
                "advertisement": "廣告",
                "website": "官方網站",
            }

            type_labels = {
                "paid": "付費客戶",
                "pro_bono": "公益服務",
                "free_practice": "免費練習",
                "other": "其他",
            }

            # Source statistics
            source_counts = {}
            for client in clients:
                source_key = client.source or "unknown"
                source_name = source_labels.get(source_key, source_key or "未知")
                source_counts[source_name] = source_counts.get(source_name, 0) + 1

            source_distribution = [
                {"name": name, "value": count} for name, count in source_counts.items()
            ]

            # Type statistics
            type_counts = {}
            for client in clients:
                type_key = client.client_type or "unknown"
                type_name = type_labels.get(type_key, type_key or "未知")
                type_counts[type_name] = type_counts.get(type_name, 0) + 1

            type_distribution = [
                {"name": name, "value": count} for name, count in type_counts.items()
            ]

            # Issue type statistics
            issue_counts = {}
            for client in clients:
                if client.issue_types:
                    issues = [issue.strip() for issue in client.issue_types.split(",")]
                    for issue in issues:
                        if issue:
                            issue_counts[issue] = issue_counts.get(issue, 0) + 1
                else:
                    issue_counts["未知"] = issue_counts.get("未知", 0) + 1

            issue_distribution = [
                {"name": name, "value": count} for name, count in issue_counts.items()
            ]

        return {
            "source_distribution": source_distribution,
            "type_distribution": type_distribution,
            "issue_distribution": issue_distribution,
        }


class ClientCreationUseCase:
    """Use case for creating new clients."""

    def __init__(self, client_repo: ClientRepoPort, user_repo: UserRepoPort):
        """Initialize use case with repository dependencies.

        Args:
            client_repo: Client repository implementation
            user_repo: User repository implementation
        """
        self.client_repo = client_repo
        self.user_repo = user_repo

    def create_client(
        self,
        coach_id: UUID,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        memo: Optional[str] = None,
        source: Optional[str] = None,
        client_type: Optional[str] = None,
        issue_types: Optional[str] = None,
        status: str = "first_session",
    ) -> Client:
        """Create a new client for a coach.

        Args:
            coach_id: UUID of the coach creating the client
            name: Client name (required)
            email: Optional email address
            phone: Optional phone number
            memo: Optional memo/notes
            source: Optional source (referral, organic, etc.)
            client_type: Optional type (paid, pro_bono, etc.)
            issue_types: Optional comma-separated issue types
            status: Client status (default: first_session)

        Returns:
            Created Client domain entity

        Raises:
            ValueError: If coach doesn't exist or email already exists
        """
        # Verify coach exists
        coach = self.user_repo.get_by_id(coach_id)
        if not coach:
            raise ValueError(f"Coach with ID {coach_id} not found")

        # Check for duplicate email if provided
        if email:
            if self.client_repo.check_email_exists_for_coach(coach_id, email):
                raise ValueError("A client with this email already exists")

        # Create client domain entity
        client = Client(
            user_id=coach_id,
            name=name,
            email=email,
            phone=phone,
            memo=memo,
            source=source,
            client_type=client_type,
            issue_types=issue_types,
            status=status,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        return self.client_repo.save(client)


class ClientUpdateUseCase:
    """Use case for updating existing clients."""

    def __init__(self, client_repo: ClientRepoPort, user_repo: UserRepoPort):
        """Initialize use case with repository dependencies.

        Args:
            client_repo: Client repository implementation
            user_repo: User repository implementation
        """
        self.client_repo = client_repo
        self.user_repo = user_repo

    def update_client(
        self,
        client_id: UUID,
        coach_id: UUID,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        memo: Optional[str] = None,
        source: Optional[str] = None,
        client_type: Optional[str] = None,
        issue_types: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Client:
        """Update an existing client.

        Args:
            client_id: UUID of the client to update
            coach_id: UUID of the coach updating the client
            name: Optional new name
            email: Optional new email
            phone: Optional new phone
            memo: Optional new memo
            source: Optional new source
            client_type: Optional new client type
            issue_types: Optional new issue types
            status: Optional new status

        Returns:
            Updated Client domain entity

        Raises:
            ValueError: If client not found, not owned by coach, anonymized, or email conflict
        """
        # Get existing client with ownership check
        client = self.client_repo.get_client_with_ownership_check(client_id, coach_id)
        if not client:
            raise ValueError("Client not found")

        if client.is_anonymized:
            raise ValueError("Cannot edit anonymized client")

        # Check for duplicate email if email is being updated
        if email and email != client.email:
            if self.client_repo.check_email_exists_for_coach(
                coach_id, email, client_id
            ):
                raise ValueError("A client with this email already exists")

        # Update fields (only if provided)
        if name is not None:
            client.name = name
        if email is not None:
            client.email = email
        if phone is not None:
            client.phone = phone
        if memo is not None:
            client.memo = memo
        if source is not None:
            client.source = source
        if client_type is not None:
            client.client_type = client_type
        if issue_types is not None:
            client.issue_types = issue_types
        if status is not None:
            client.status = status

        client.updated_at = datetime.now(UTC)

        return self.client_repo.save(client)


class ClientDeletionUseCase:
    """Use case for deleting and anonymizing clients."""

    def __init__(self, client_repo: ClientRepoPort, user_repo: UserRepoPort):
        """Initialize use case with repository dependencies.

        Args:
            client_repo: Client repository implementation
            user_repo: User repository implementation
        """
        self.client_repo = client_repo
        self.user_repo = user_repo

    def delete_client(self, client_id: UUID, coach_id: UUID) -> bool:
        """Delete a client (hard delete, only if no sessions).

        Args:
            client_id: UUID of the client to delete
            coach_id: UUID of the coach deleting the client

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If client not found, not owned by coach, or has sessions
        """
        # Get existing client with ownership check
        client = self.client_repo.get_client_with_ownership_check(client_id, coach_id)
        if not client:
            raise ValueError("Client not found")

        # TODO: Check if client has coaching sessions once CoachingSessionRepo is implemented
        # For now, we'll allow deletion - this is a business rule that should be enforced
        # session_count = self.coaching_session_repo.count_by_client_id(client_id)
        # if session_count > 0:
        #     raise ValueError("Cannot delete client with existing sessions. Use anonymization instead.")

        return self.client_repo.delete(client_id)

    def anonymize_client(self, client_id: UUID, coach_id: UUID) -> str:
        """Anonymize a client for GDPR compliance.

        Args:
            client_id: UUID of the client to anonymize
            coach_id: UUID of the coach requesting anonymization

        Returns:
            Message with the anonymized name

        Raises:
            ValueError: If client not found, not owned by coach, or already anonymized
        """
        # Get existing client with ownership check
        client = self.client_repo.get_client_with_ownership_check(client_id, coach_id)
        if not client:
            raise ValueError("Client not found")

        if client.is_anonymized:
            raise ValueError("Client is already anonymized")

        # Get next anonymous number for this coach
        anonymous_count = self.client_repo.get_anonymized_count_for_coach(coach_id)
        next_number = anonymous_count + 1

        # Anonymize the client using domain logic
        client.anonymize(next_number)
        client.updated_at = datetime.now(UTC)

        # Save the anonymized client
        updated_client = self.client_repo.save(client)

        return f"Client anonymized as '{updated_client.name}'"


class ClientOptionsUseCase:
    """Use case for getting client option lists."""

    def get_source_options(self) -> List[Dict[str, str]]:
        """Get available client source options.

        Returns:
            List of source options with value and labelKey
        """
        return [
            {"value": "referral", "labelKey": "clients.sourceReferral"},
            {"value": "organic", "labelKey": "clients.sourceOrganic"},
            {"value": "friend", "labelKey": "clients.sourceFriend"},
            {"value": "social_media", "labelKey": "clients.sourceSocialMedia"},
        ]

    def get_type_options(self) -> List[Dict[str, str]]:
        """Get available client type options.

        Returns:
            List of type options with value and labelKey
        """
        return [
            {"value": "paid", "labelKey": "clients.typePaid"},
            {"value": "pro_bono", "labelKey": "clients.typeProBono"},
            {"value": "free_practice", "labelKey": "clients.typeFreePractice"},
            {"value": "other", "labelKey": "clients.typeOther"},
        ]

    def get_status_options(self) -> List[Dict[str, str]]:
        """Get available client status options.

        Returns:
            List of status options with value and label
        """
        return [
            {"value": "first_session", "label": "首次會談"},
            {"value": "in_progress", "label": "進行中"},
            {"value": "paused", "label": "暫停"},
            {"value": "completed", "label": "結案"},
        ]
