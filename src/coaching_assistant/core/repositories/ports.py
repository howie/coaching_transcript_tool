"""Repository interfaces and ports for Clean Architecture.

This module defines Protocol interfaces for all data access operations,
ensuring the core business logic is decoupled from infrastructure concerns.

Following the Repository pattern and Dependency Inversion Principle.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Protocol
from uuid import UUID

from ..models.client import Client
from ..models.coach_profile import CoachProfile
from ..models.coaching_plan import CoachingPlan
from ..models.coaching_session import CoachingSession
from ..models.plan_configuration import PlanConfiguration
from ..models.session import Session, SessionStatus
from ..models.subscription import (
    ECPayCreditAuthorization,
    SaasSubscription,
    SubscriptionPayment,
    SubscriptionStatus,
)
from ..models.transcript import SegmentRole, SessionRole, TranscriptSegment
from ..models.usage_analytics import UsageAnalytics
from ..models.usage_history import UsageHistory
from ..models.usage_log import UsageLog

# Domain types - using pure domain models only (Clean Architecture compliant)
from ..models.user import User, UserPlan


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

    def get_by_id(self, session_id: UUID) -> Optional[Session]:
        """Get session by ID."""
        ...

    def get_by_user_id(
        self,
        user_id: UUID,
        status: Optional[SessionStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Session]:
        """Get sessions by user ID with optional filtering."""
        ...

    def save(self, session: Session) -> Session:
        """Save or update session entity."""
        ...

    def update_status(self, session_id: UUID, status: SessionStatus) -> Session:
        """Update session status."""
        ...

    def get_sessions_by_date_range(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Session]:
        """Get sessions within date range for user."""
        ...

    def count_user_sessions(
        self, user_id: UUID, since: Optional[datetime] = None
    ) -> int:
        """Count user sessions, optionally since a date."""
        ...

    def get_total_duration_minutes(
        self, user_id: UUID, since: Optional[datetime] = None
    ) -> int:
        """Get total duration in minutes for user sessions."""
        ...

    def get_completed_count_for_user(self, user_id: UUID) -> int:
        """Get count of completed sessions for a user."""
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

    def create(self, usage_log: "UsageLog") -> "UsageLog":
        """Create a new usage log entry."""
        ...

    def get_by_user_and_timeframe(
        self, user_id: UUID, start_date: datetime, end_date: datetime
    ) -> List["UsageLog"]:
        """Get usage logs for a user within a timeframe."""
        ...

    def get_total_usage_for_user_this_month(self, user_id: UUID) -> Dict[str, Any]:
        """Get total usage metrics for user in current month."""
        ...

    def get_user_usage_history(self, user_id: UUID, months: int) -> Dict[str, Any]:
        """Get user usage history for specified number of months."""
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

    def get_with_ownership_check(
        self, session_id: UUID, coach_id: UUID
    ) -> Optional[CoachingSession]:
        """Get coaching session with ownership verification."""
        ...

    def get_paginated_with_filters(
        self,
        coach_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        client_id: Optional[UUID] = None,
        currency: Optional[str] = None,
        sort: str = "-session_date",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[CoachingSession], int]:
        """Get paginated coaching sessions with filtering and sorting."""
        ...

    def get_last_session_by_client(
        self, coach_id: UUID, client_id: UUID
    ) -> Optional[CoachingSession]:
        """Get the most recent coaching session for a specific client."""
        ...

    def get_total_minutes_for_user(self, user_id: UUID) -> int:
        """Get total minutes from all coaching sessions for a user."""
        ...

    def get_monthly_minutes_for_user(self, user_id: UUID, year: int, month: int) -> int:
        """Get total minutes for a user in a specific month."""
        ...

    def get_monthly_revenue_by_currency(
        self, user_id: UUID, year: int, month: int
    ) -> Dict[str, int]:
        """Get revenue by currency for a user in a specific month."""
        ...

    def get_unique_clients_count_for_user(self, user_id: UUID) -> int:
        """Get count of unique clients for a user."""
        ...


class CoachProfileRepoPort(Protocol):
    """Repository interface for CoachProfile entity operations."""

    def get_by_user_id(self, user_id: UUID) -> Optional[CoachProfile]:
        """Get coach profile by user ID."""
        ...

    def save(self, profile: CoachProfile) -> CoachProfile:
        """Save or update coach profile."""
        ...

    def delete(self, user_id: UUID) -> bool:
        """Delete coach profile by user ID."""
        ...

    def get_all_verified_coaches(self) -> List[CoachProfile]:
        """Get all verified coach profiles."""
        ...

    # CoachingPlan operations
    def get_coaching_plans_by_profile_id(self, profile_id: UUID) -> List[CoachingPlan]:
        """Get all coaching plans for a profile."""
        ...

    def get_coaching_plan_by_id(self, plan_id: UUID) -> Optional[CoachingPlan]:
        """Get coaching plan by ID."""
        ...

    def save_coaching_plan(self, plan: CoachingPlan) -> CoachingPlan:
        """Save or update coaching plan."""
        ...

    def delete_coaching_plan(self, plan_id: UUID) -> bool:
        """Delete coaching plan by ID."""
        ...


class TranscriptRepoPort(Protocol):
    """Repository interface for TranscriptSegment entity operations."""

    def get_by_session_id(self, session_id: UUID) -> List[TranscriptSegment]:
        """Get all transcript segments for a session."""
        ...

    def save_segments(
        self, segments: List[TranscriptSegment]
    ) -> List[TranscriptSegment]:
        """Save multiple transcript segments."""
        ...

    def update_speaker_roles(
        self, session_id: UUID, role_mappings: Dict[str, str]
    ) -> List[TranscriptSegment]:
        """Update speaker roles for session segments."""
        ...

    def update_segment_content(
        self, session_id: UUID, segments: List[TranscriptSegment]
    ) -> List[TranscriptSegment]:
        """Update content for existing transcript segments."""
        ...


class UsageAnalyticsRepoPort(Protocol):
    """Repository interface for UsageAnalytics entity operations."""

    def get_or_create_monthly(
        self, user_id: UUID, year: int, month: int
    ) -> "UsageAnalytics":
        """Get or create monthly analytics record."""
        ...

    def update(self, analytics: "UsageAnalytics") -> "UsageAnalytics":
        """Update analytics record."""
        ...

    def get_by_user(self, user_id: UUID) -> List["UsageAnalytics"]:
        """Get all analytics records for a user."""
        ...

    def get_admin_analytics(self) -> Dict[str, Any]:
        """Get system-wide analytics for admin users."""
        ...

    def get_by_month_year(self, month_year: str) -> List["UsageAnalytics"]:
        """Get all analytics records for a specific month."""
        ...


# Already defined above - removing duplicate


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


class SpeakerRoleRepoPort(Protocol):
    """Repository interface for SessionRole entity operations (speaker-level roles)."""

    def get_by_session_id(self, session_id: UUID) -> List["SessionRole"]:
        """Get all speaker role assignments for a session."""
        ...

    def save_speaker_roles(
        self, session_id: UUID, speaker_roles: List["SessionRole"]
    ) -> List["SessionRole"]:
        """Save or update speaker role assignments for a session."""
        ...

    def delete_by_session_id(self, session_id: UUID) -> None:
        """Delete all speaker role assignments for a session."""
        ...


class SegmentRoleRepoPort(Protocol):
    """Repository interface for SegmentRole entity operations (segment-level roles)."""

    def get_by_session_id(self, session_id: UUID) -> List["SegmentRole"]:
        """Get all segment role assignments for a session."""
        ...

    def save_segment_roles(
        self, session_id: UUID, segment_roles: List["SegmentRole"]
    ) -> List["SegmentRole"]:
        """Save or update segment role assignments for a session."""
        ...

    def delete_by_session_id(self, session_id: UUID) -> None:
        """Delete all segment role assignments for a session."""
        ...


class NotificationPort(Protocol):
    """Port interface for notification services following Clean Architecture."""

    async def send_payment_failure_notification(
        self, user_email: str, payment_details: Dict[str, Any]
    ) -> bool:
        """Send payment failure notification."""
        ...

    async def send_payment_retry_notification(
        self, user_email: str, retry_details: Dict[str, Any]
    ) -> bool:
        """Send payment retry notification."""
        ...

    async def send_subscription_cancellation_notification(
        self, user_email: str, cancellation_details: Dict[str, Any]
    ) -> bool:
        """Send subscription cancellation notification."""
        ...

    async def send_plan_downgrade_notification(
        self, user_email: str, downgrade_details: Dict[str, Any]
    ) -> bool:
        """Send plan downgrade notification."""
        ...


class ECPayClientPort(Protocol):
    """Port interface for ECPay API client following Clean Architecture."""

    async def cancel_credit_authorization(
        self, auth_code: str, merchant_trade_no: str
    ) -> Dict[str, Any]:
        """Cancel ECPay credit card authorization."""
        ...

    async def retry_payment(
        self, auth_code: str, merchant_trade_no: str, amount: int
    ) -> Dict[str, Any]:
        """Retry payment for failed ECPay transaction."""
        ...

    async def process_payment(
        self, merchant_trade_no: str, amount: int, item_name: str
    ) -> Dict[str, Any]:
        """Process new payment via ECPay."""
        ...

    def calculate_refund_amount(
        self, original_amount: int, days_used: int, total_days: int
    ) -> int:
        """Calculate prorated refund amount."""
        ...


class AdminAnalyticsRepoPort(Protocol):
    """Repository interface for admin analytics and reporting operations."""

    def get_total_users_count(self) -> int:
        """Get total count of all users."""
        ...

    def get_new_users_in_period(
        self, start: datetime, end: datetime
    ) -> List[Dict[str, Any]]:
        """Get new users created within the specified period."""
        ...

    def get_active_users_count(self, start: datetime, end: datetime) -> int:
        """Get count of users who created sessions in the period."""
        ...

    def get_users_by_plan_distribution(self) -> Dict[str, int]:
        """Get user count distribution by plan type."""
        ...

    def get_session_metrics_for_period(
        self, start: datetime, end: datetime
    ) -> Dict[str, Any]:
        """Get comprehensive session metrics for the specified period."""
        ...

    def get_admin_users_list(self) -> List[Dict[str, Any]]:
        """Get list of all admin and staff users."""
        ...

    def get_staff_logins_count(self, start: datetime, end: datetime) -> int:
        """Get count of staff logins in the specified period."""
        ...

    def get_subscription_metrics(
        self, start: datetime, end: datetime
    ) -> Dict[str, Any]:
        """Get subscription and billing metrics for the specified period."""
        ...

    def get_system_health_metrics(
        self, start: datetime, end: datetime
    ) -> Dict[str, Any]:
        """Get system health and performance metrics."""
        ...

    def get_top_active_users(
        self, start: datetime, end: datetime, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top users by activity in the specified period."""
        ...
