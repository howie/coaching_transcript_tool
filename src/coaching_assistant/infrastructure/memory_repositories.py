"""In-memory repository implementations for testing.

These repositories store data in memory dictionaries and provide
the same interface as the SQLAlchemy repositories. They are perfect
for unit testing business logic without database dependencies.
"""

import copy
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from ..core.repositories.ports import (
    SessionRepoPort,
    UsageLogRepoPort,
    UserRepoPort,
)
from ..models.session import Session as SessionModel
from ..models.session import SessionStatus
from ..models.usage_log import TranscriptionType, UsageLog
from ..models.user import User, UserPlan


class InMemoryUserRepository(UserRepoPort):
    """In-memory implementation of UserRepoPort for testing."""

    def __init__(self):
        """Initialize empty repository."""
        self._users: Dict[UUID, User] = {}
        self._email_index: Dict[str, UUID] = {}

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        user = self._users.get(user_id)
        return copy.deepcopy(user) if user else None

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        user_id = self._email_index.get(email)
        if user_id:
            return copy.deepcopy(self._users.get(user_id))
        return None

    def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email."""
        return email in self._email_index

    def save(self, user: User) -> User:
        """Save or update user entity."""
        # Generate ID if new user
        if user.id is None:
            user.id = uuid4()

        # Update timestamps
        if user.id not in self._users:
            user.created_at = datetime.now(UTC)
        user.updated_at = datetime.now(UTC)

        # Store user and update email index
        stored_user = copy.deepcopy(user)
        self._users[user.id] = stored_user
        self._email_index[user.email] = user.id

        return copy.deepcopy(stored_user)

    def delete(self, user_id: UUID) -> bool:
        """Delete user by ID."""
        user = self._users.get(user_id)
        if not user:
            return False

        # Remove from email index
        self._email_index.pop(user.email, None)

        # Remove user
        del self._users[user_id]
        return True

    def get_all_active_users(self) -> List[User]:
        """Get all active users."""
        active_users = [
            copy.deepcopy(user) for user in self._users.values() if user.is_active
        ]
        return sorted(active_users, key=lambda u: u.created_at)

    def update_plan(self, user_id: UUID, plan: UserPlan) -> User:
        """Update user's subscription plan."""
        user = self._users.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        user.plan = plan
        user.updated_at = datetime.now(UTC)

        return copy.deepcopy(user)

    def clear(self) -> None:
        """Clear all data - useful for testing."""
        self._users.clear()
        self._email_index.clear()


class InMemoryUsageLogRepository(UsageLogRepoPort):
    """In-memory implementation of UsageLogRepoPort for testing."""

    def __init__(self):
        """Initialize empty repository."""
        self._logs: Dict[UUID, UsageLog] = {}
        self._session_index: Dict[UUID, List[UUID]] = defaultdict(list)
        self._user_index: Dict[UUID, List[UUID]] = defaultdict(list)

    def save(self, usage_log: UsageLog) -> UsageLog:
        """Save usage log entry."""
        # Generate ID if new log
        if usage_log.id is None:
            usage_log.id = uuid4()

        # Update timestamps
        if usage_log.id not in self._logs:
            usage_log.created_at = datetime.now(UTC)
        usage_log.updated_at = datetime.now(UTC)

        # Store log
        stored_log = copy.deepcopy(usage_log)
        self._logs[usage_log.id] = stored_log

        # Update indexes
        if usage_log.session_id:
            if usage_log.id not in self._session_index[usage_log.session_id]:
                self._session_index[usage_log.session_id].append(usage_log.id)

        if usage_log.user_id:
            if usage_log.id not in self._user_index[usage_log.user_id]:
                self._user_index[usage_log.user_id].append(usage_log.id)

        return copy.deepcopy(stored_log)

    def get_by_session_id(self, session_id: UUID) -> List[UsageLog]:
        """Get all usage logs for a session."""
        log_ids = self._session_index.get(session_id, [])
        logs = [
            copy.deepcopy(self._logs[log_id])
            for log_id in log_ids
            if log_id in self._logs
        ]
        return sorted(logs, key=lambda log: log.created_at)

    def get_by_user_id(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[UsageLog]:
        """Get usage logs for user within optional date range."""
        log_ids = self._user_index.get(user_id, [])
        logs = [
            copy.deepcopy(self._logs[log_id])
            for log_id in log_ids
            if log_id in self._logs
        ]

        # Apply date filters
        if start_date:
            logs = [log for log in logs if log.created_at >= start_date]
        if end_date:
            logs = [log for log in logs if log.created_at <= end_date]

        return sorted(logs, key=lambda log: log.created_at)

    def get_total_cost_for_user(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Decimal:
        """Calculate total cost for user within date range."""
        logs = self.get_by_user_id(user_id, start_date, end_date)
        billable_logs = [log for log in logs if log.is_billable]

        total = sum(log.cost_usd for log in billable_logs if log.cost_usd)
        return total or Decimal("0.00")

    def get_usage_summary(
        self, user_id: UUID, period_start: datetime, period_end: datetime
    ) -> Dict[str, any]:
        """Get aggregated usage summary for user in time period."""
        logs = self.get_by_user_id(user_id, period_start, period_end)

        # Calculate totals
        total_sessions = len(logs)
        total_duration = sum(log.duration_minutes for log in logs)
        billable_logs = [log for log in logs if log.is_billable]
        total_cost = sum(
            log.cost_usd for log in billable_logs if log.cost_usd
        ) or Decimal("0.00")

        # Transcription type breakdown
        type_breakdown = {}
        for transcription_type in TranscriptionType:
            count = len(
                [log for log in logs if log.transcription_type == transcription_type]
            )
            type_breakdown[transcription_type.value] = count

        # STT provider breakdown
        provider_breakdown = {}
        for log in logs:
            if log.stt_provider:
                provider_breakdown[log.stt_provider] = (
                    provider_breakdown.get(log.stt_provider, 0) + 1
                )

        return {
            "total_sessions": total_sessions,
            "total_duration_minutes": total_duration,
            "total_cost_usd": float(total_cost),
            "transcription_type_breakdown": type_breakdown,
            "stt_provider_breakdown": provider_breakdown,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
        }

    def clear(self) -> None:
        """Clear all data - useful for testing."""
        self._logs.clear()
        self._session_index.clear()
        self._user_index.clear()


class InMemorySessionRepository(SessionRepoPort):
    """In-memory implementation of SessionRepoPort for testing."""

    def __init__(self):
        """Initialize empty repository."""
        self._sessions: Dict[UUID, SessionModel] = {}
        self._user_index: Dict[UUID, List[UUID]] = defaultdict(list)

    def get_by_id(self, session_id: UUID) -> Optional[SessionModel]:
        """Get session by ID."""
        session = self._sessions.get(session_id)
        return copy.deepcopy(session) if session else None

    def get_by_user_id(
        self,
        user_id: UUID,
        status: Optional[SessionStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[SessionModel]:
        """Get sessions by user ID with optional filtering."""
        session_ids = self._user_index.get(user_id, [])
        sessions = [
            copy.deepcopy(self._sessions[sid])
            for sid in session_ids
            if sid in self._sessions
        ]

        # Apply status filter
        if status:
            sessions = [s for s in sessions if s.status == status]

        # Sort by created_at desc
        sessions.sort(key=lambda s: s.created_at, reverse=True)

        # Apply pagination
        return sessions[offset : offset + limit]

    def save(self, session_model: SessionModel) -> SessionModel:
        """Save or update session entity."""
        # Generate ID if new session
        if session_model.id is None:
            session_model.id = uuid4()

        # Update timestamps
        if session_model.id not in self._sessions:
            session_model.created_at = datetime.now(UTC)
        session_model.updated_at = datetime.now(UTC)

        # Store session
        stored_session = copy.deepcopy(session_model)
        self._sessions[session_model.id] = stored_session

        # Update user index
        if session_model.user_id:
            if session_model.id not in self._user_index[session_model.user_id]:
                self._user_index[session_model.user_id].append(session_model.id)

        return copy.deepcopy(stored_session)

    def update_status(self, session_id: UUID, status: SessionStatus) -> SessionModel:
        """Update session status."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.status = status
        session.updated_at = datetime.now(UTC)

        return copy.deepcopy(session)

    def get_sessions_by_date_range(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> List[SessionModel]:
        """Get sessions within date range for user."""
        session_ids = self._user_index.get(user_id, [])
        sessions = [
            copy.deepcopy(self._sessions[sid])
            for sid in session_ids
            if sid in self._sessions
        ]

        # Apply date filter
        filtered_sessions = [
            s for s in sessions if start_date <= s.created_at <= end_date
        ]

        return sorted(filtered_sessions, key=lambda s: s.created_at)

    def count_user_sessions(
        self, user_id: UUID, since: Optional[datetime] = None
    ) -> int:
        """Count user sessions, optionally since a date."""
        session_ids = self._user_index.get(user_id, [])
        sessions = [self._sessions[sid] for sid in session_ids if sid in self._sessions]

        if since:
            sessions = [s for s in sessions if s.created_at >= since]

        return len(sessions)

    def get_total_duration_minutes(
        self, user_id: UUID, since: Optional[datetime] = None
    ) -> int:
        """Get total duration in minutes for user sessions."""
        session_ids = self._user_index.get(user_id, [])
        sessions = [self._sessions[sid] for sid in session_ids if sid in self._sessions]

        if since:
            sessions = [s for s in sessions if s.created_at >= since]

        total_seconds = sum(
            s.duration_seconds for s in sessions if s.duration_seconds is not None
        )

        return int(total_seconds / 60)

    def clear(self) -> None:
        """Clear all data - useful for testing."""
        self._sessions.clear()
        self._user_index.clear()


# Factory functions for easy creation
def create_in_memory_user_repository() -> UserRepoPort:
    """Create an in-memory user repository for testing."""
    return InMemoryUserRepository()


def create_in_memory_usage_log_repository() -> UsageLogRepoPort:
    """Create an in-memory usage log repository for testing."""
    return InMemoryUsageLogRepository()


def create_in_memory_session_repository() -> SessionRepoPort:
    """Create an in-memory session repository for testing."""
    return InMemorySessionRepository()
