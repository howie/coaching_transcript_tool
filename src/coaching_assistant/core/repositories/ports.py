"""Repository interfaces and ports for Clean Architecture.

This module defines Protocol interfaces for all data access operations,
ensuring the core business logic is decoupled from infrastructure concerns.

Following the Repository pattern and Dependency Inversion Principle.
"""

from __future__ import annotations
from typing import Protocol, Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

# Domain types - these will eventually move to a dedicated domain module
from ...models.user import User, UserPlan
from ...models.session import Session as SessionModel, SessionStatus
from ...models.usage_log import UsageLog, TranscriptionType
from ...models.usage_history import UsageHistory
from ...models.usage_analytics import UsageAnalytics
from ...models.plan_configuration import PlanConfiguration
from ...models.ecpay_subscription import (
    SaasSubscription,
    SubscriptionPayment,
    ECPayCreditAuthorization,
    SubscriptionStatus,
    PaymentStatus,
    ECPayAuthStatus,
)
from ...models.client import Client
from ...models.coaching_session import CoachingSession
from ...models.coach_profile import CoachProfile
from ...models.transcript import TranscriptSegment


class UserRepoPort(Protocol):
    """Repository interface for User entity operations."""

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        ...

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        ...

    def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email."""
        ...

    def save(self, user: User) -> User:
        """Save or update user entity."""
        ...

    def delete(self, user_id: UUID) -> bool:
        """Delete user by ID. Returns True if deleted."""
        ...

    def get_all_active_users(self) -> List[User]:
        """Get all active users."""
        ...

    def update_plan(self, user_id: UUID, plan: UserPlan) -> User:
        """Update user's subscription plan."""
        ...


class SessionRepoPort(Protocol):
    """Repository interface for transcription Session entity operations."""

    def get_by_id(self, session_id: UUID) -> Optional[SessionModel]:
        """Get session by ID."""
        ...

    def get_by_user_id(
        self,
        user_id: UUID,
        status: Optional[SessionStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[SessionModel]:
        """Get sessions by user ID with optional filtering."""
        ...

    def save(self, session: SessionModel) -> SessionModel:
        """Save or update session entity."""
        ...

    def update_status(self, session_id: UUID, status: SessionStatus) -> SessionModel:
        """Update session status."""
        ...

    def get_sessions_by_date_range(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> List[SessionModel]:
        """Get sessions within date range for user."""
        ...

    def count_user_sessions(self, user_id: UUID, since: Optional[datetime] = None) -> int:
        """Count user sessions, optionally since a date."""
        ...

    def get_total_duration_minutes(
        self, user_id: UUID, since: Optional[datetime] = None
    ) -> int:
        """Get total duration in minutes for user sessions."""
        ...


class UsageLogRepoPort(Protocol):
    """Repository interface for UsageLog entity operations."""

    def save(self, usage_log: UsageLog) -> UsageLog:
        """Save usage log entry."""
        ...

    def get_by_session_id(self, session_id: UUID) -> List[UsageLog]:
        """Get all usage logs for a session."""
        ...

    def get_by_user_id(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[UsageLog]:
        """Get usage logs for user within optional date range."""
        ...

    def get_total_cost_for_user(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Decimal:
        """Calculate total cost for user within date range."""
        ...

    def get_usage_summary(
        self, user_id: UUID, period_start: datetime, period_end: datetime
    ) -> Dict[str, Any]:
        """Get aggregated usage summary for user in time period."""
        ...


class UsageHistoryRepoPort(Protocol):
    """Repository interface for UsageHistory entity operations."""

    def save(self, usage_history: UsageHistory) -> UsageHistory:
        """Save usage history snapshot."""
        ...

    def get_by_user_and_period(
        self,
        user_id: UUID,
        period_type: str,
        period_start: datetime,
    ) -> Optional[UsageHistory]:
        """Get usage history for specific period."""
        ...

    def get_trends_for_user(
        self,
        user_id: UUID,
        period_type: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[UsageHistory]:
        """Get usage trends for user across time periods."""
        ...


class PlanConfigurationRepoPort(Protocol):
    """Repository interface for PlanConfiguration entity operations."""

    def get_by_plan_type(self, plan_type: UserPlan) -> Optional[PlanConfiguration]:
        """Get plan configuration by plan type."""
        ...

    def get_all_active_plans(self) -> List[PlanConfiguration]:
        """Get all active plan configurations."""
        ...

    def save(self, plan_config: PlanConfiguration) -> PlanConfiguration:
        """Save or update plan configuration."""
        ...


class SubscriptionRepoPort(Protocol):
    """Repository interface for subscription-related entities."""

    def get_subscription_by_user_id(self, user_id: UUID) -> Optional[SaasSubscription]:
        """Get active subscription for user."""
        ...

    def save_subscription(self, subscription: SaasSubscription) -> SaasSubscription:
        """Save or update subscription."""
        ...

    def get_credit_authorization_by_user_id(
        self, user_id: UUID
    ) -> Optional[ECPayCreditAuthorization]:
        """Get credit authorization for user."""
        ...

    def save_credit_authorization(
        self, auth: ECPayCreditAuthorization
    ) -> ECPayCreditAuthorization:
        """Save or update credit authorization."""
        ...

    def save_payment(self, payment: SubscriptionPayment) -> SubscriptionPayment:
        """Save subscription payment record."""
        ...

    def get_payments_for_subscription(
        self, subscription_id: UUID
    ) -> List[SubscriptionPayment]:
        """Get all payments for a subscription."""
        ...

    def update_subscription_status(
        self, subscription_id: UUID, status: SubscriptionStatus
    ) -> SaasSubscription:
        """Update subscription status."""
        ...


class ClientRepoPort(Protocol):
    """Repository interface for Client entity operations."""

    def get_by_id(self, client_id: UUID) -> Optional[Client]:
        """Get client by ID."""
        ...

    def get_by_coach_id(self, coach_id: UUID) -> List[Client]:
        """Get all clients for a coach."""
        ...

    def save(self, client: Client) -> Client:
        """Save or update client entity."""
        ...

    def delete(self, client_id: UUID) -> bool:
        """Delete client by ID."""
        ...

    def search_clients(
        self, coach_id: UUID, query: str, limit: int = 50
    ) -> List[Client]:
        """Search clients by name or email for a coach."""
        ...


class CoachingSessionRepoPort(Protocol):
    """Repository interface for CoachingSession entity operations."""

    def get_by_id(self, session_id: UUID) -> Optional[CoachingSession]:
        """Get coaching session by ID."""
        ...

    def get_by_coach_id(
        self,
        coach_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[CoachingSession]:
        """Get coaching sessions for a coach."""
        ...

    def get_by_client_id(
        self,
        client_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[CoachingSession]:
        """Get coaching sessions for a client."""
        ...

    def save(self, session: CoachingSession) -> CoachingSession:
        """Save or update coaching session."""
        ...

    def delete(self, session_id: UUID) -> bool:
        """Delete coaching session by ID."""
        ...


class CoachProfileRepoPort(Protocol):
    """Repository interface for CoachProfile entity operations."""

    def get_by_user_id(self, user_id: UUID) -> Optional[CoachProfile]:
        """Get coach profile by user ID."""
        ...

    def save(self, profile: CoachProfile) -> CoachProfile:
        """Save or update coach profile."""
        ...

    def get_all_verified_coaches(self) -> List[CoachProfile]:
        """Get all verified coach profiles."""
        ...


class TranscriptRepoPort(Protocol):
    """Repository interface for TranscriptSegment entity operations."""

    def get_by_session_id(self, session_id: UUID) -> List[TranscriptSegment]:
        """Get all transcript segments for a session."""
        ...

    def save_segments(self, segments: List[TranscriptSegment]) -> List[TranscriptSegment]:
        """Save multiple transcript segments."""
        ...

    def update_speaker_roles(
        self, session_id: UUID, role_mappings: Dict[str, str]
    ) -> List[TranscriptSegment]:
        """Update speaker roles for session segments."""
        ...

    def delete_by_session_id(self, session_id: UUID) -> bool:
        """Delete all segments for a session."""
        ...


# Aggregate repository interfaces for complex operations
class UsageAnalyticsRepoPort(Protocol):
    """Repository interface for complex usage analytics operations."""

    def get_user_usage_analytics(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> Optional[UsageAnalytics]:
        """Get or create usage analytics for user in period."""
        ...

    def save_analytics(self, analytics: UsageAnalytics) -> UsageAnalytics:
        """Save usage analytics entity."""
        ...

    def get_system_wide_analytics(
        self, start_date: datetime, end_date: datetime
    ) -> List[UsageAnalytics]:
        """Get system-wide analytics across all users."""
        ...

    def get_plan_analytics(
        self, plan_type: UserPlan, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get aggregated analytics by plan type."""
        ...


# Unit of Work interface for transaction management
class UnitOfWorkPort(Protocol):
    """Unit of Work interface for transaction management."""

    def __enter__(self) -> UnitOfWorkPort:
        """Start transaction context."""
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """End transaction context, rollback on exception."""
        ...

    def commit(self) -> None:
        """Commit current transaction."""
        ...

    def rollback(self) -> None:
        """Rollback current transaction."""
        ...

    # Repository access within unit of work
    @property
    def users(self) -> UserRepoPort:
        """Get user repository."""
        ...

    @property
    def sessions(self) -> SessionRepoPort:
        """Get session repository."""
        ...

    @property
    def usage_logs(self) -> UsageLogRepoPort:
        """Get usage log repository."""
        ...

    @property
    def subscriptions(self) -> SubscriptionRepoPort:
        """Get subscription repository."""
        ...