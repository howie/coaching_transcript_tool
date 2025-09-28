"""UserModel ORM with domain model conversion."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import relationship

from ....core.models.user import User, UserPlan, UserRole
from .base import BaseModel


class UserModel(BaseModel):
    """ORM model for User entity with SQLAlchemy mappings."""

    __tablename__ = "user"

    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable for SSO users

    # Profile fields
    name = Column(String(255), nullable=False)
    avatar_url = Column(String(512))

    # Plan and permissions (persist enum values to match legacy schema)
    plan = Column(
        Enum(UserPlan, values_callable=lambda x: [e.value for e in x]),
        default=UserPlan.FREE,
        nullable=False,
    )
    role = Column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.USER,
        nullable=False,
    )

    # Usage tracking
    usage_minutes = Column(Integer, default=0, nullable=False)
    session_count = Column(Integer, default=0, nullable=False)

    # Activity tracking
    last_active_at = Column(DateTime)

    # Subscription information
    stripe_customer_id = Column(String(255), unique=True)
    subscription_status = Column(String(50))  # active, canceled, past_due, etc.

    # Billing information
    billing_email = Column(String(255))
    billing_address = Column(JSON)  # Store as JSON for flexibility

    # Preferences and settings
    language_preference = Column(String(20), default="zh-TW")
    timezone = Column(String(50), default="Asia/Taipei")
    email_notifications = Column(String(20), default="enabled")
    marketing_emails = Column(String(20), default="enabled")

    # Profile completion and onboarding
    profile_completed = Column(String(20), default="pending")
    onboarding_completed = Column(String(20), default="pending")

    # Admin notes and flags
    admin_notes = Column(Text)
    is_test_user = Column(String(20), default="disabled")

    # ORM relationships (using string references to avoid circular imports)
    sessions = relationship(
        "SessionModel", back_populates="user", cascade="all, delete-orphan"
    )
    usage_logs = relationship(
        "UsageLogModel", back_populates="user", cascade="all, delete-orphan"
    )
    # Legacy relationships - will be migrated later
    # coaching_sessions = relationship("CoachingSession", back_populates="user", cascade="all, delete-orphan")
    # clients = relationship("Client", back_populates="user", cascade="all, delete-orphan")

    def to_domain(self) -> User:
        """Convert ORM model to domain model."""
        return User(
            id=UUID(str(self.id)) if self.id else None,
            email=self.email or "",
            name=self.name or "",
            hashed_password=self.hashed_password,
            avatar_url=self.avatar_url,
            plan=self.plan or UserPlan.FREE,
            role=self.role or UserRole.USER,
            usage_minutes=self.usage_minutes or 0,
            session_count=self.session_count or 0,
            created_at=self.created_at,
            updated_at=self.updated_at,
            last_active_at=self.last_active_at,
            stripe_customer_id=self.stripe_customer_id,
            subscription_status=self.subscription_status,
        )

    @classmethod
    def from_domain(cls, user: User) -> "UserModel":
        """Convert domain model to ORM model."""
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            hashed_password=user.hashed_password,
            avatar_url=user.avatar_url,
            plan=user.plan,
            role=user.role,
            usage_minutes=user.usage_minutes,
            session_count=user.session_count,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_active_at=user.last_active_at,
            stripe_customer_id=user.stripe_customer_id,
            subscription_status=user.subscription_status,
        )

    def update_from_domain(self, user: User) -> None:
        """Update ORM model fields from domain model."""
        self.email = user.email
        self.name = user.name
        self.hashed_password = user.hashed_password
        self.avatar_url = user.avatar_url
        self.plan = user.plan
        self.role = user.role
        self.usage_minutes = user.usage_minutes
        self.session_count = user.session_count
        self.last_active_at = user.last_active_at
        self.stripe_customer_id = user.stripe_customer_id
        self.subscription_status = user.subscription_status
        self.updated_at = user.updated_at or datetime.utcnow()

    # Database-specific helper methods

    def get_sessions_count(self) -> int:
        """Get total number of sessions for this user."""
        return len(self.sessions) if self.sessions else 0

    def get_total_usage_minutes(self) -> int:
        """Get total usage minutes from all usage logs."""
        if not self.usage_logs:
            return 0
        return sum(log.duration_minutes for log in self.usage_logs if log.billable)

    def get_active_sessions(self):
        """Get sessions that are currently active (not completed/failed)."""
        if not self.sessions:
            return []
        from ....core.models.session import SessionStatus

        active_statuses = [
            SessionStatus.UPLOADING,
            SessionStatus.PENDING,
            SessionStatus.PROCESSING,
        ]
        return [
            session for session in self.sessions if session.status in active_statuses
        ]

    def get_recent_sessions(self, limit: int = 10):
        """Get most recent sessions for this user."""
        if not self.sessions:
            return []
        return sorted(
            self.sessions,
            key=lambda s: s.created_at or datetime.min,
            reverse=True,
        )[:limit]

    def has_active_subscription(self) -> bool:
        """Check if user has an active subscription."""
        return self.subscription_status in ["active", "trialing"]

    def is_premium_plan(self) -> bool:
        """Check if user is on a premium plan."""
        return self.plan in [
            UserPlan.PRO,
            UserPlan.ENTERPRISE,
            UserPlan.COACHING_SCHOOL,
        ]

    def can_access_feature(self, feature: str) -> bool:
        """Check if user can access a specific feature based on plan."""
        feature_access = {
            "ai_analysis": [
                UserPlan.STUDENT,
                UserPlan.PRO,
                UserPlan.ENTERPRISE,
                UserPlan.COACHING_SCHOOL,
            ],
            "export_docx": [
                UserPlan.STUDENT,
                UserPlan.PRO,
                UserPlan.ENTERPRISE,
                UserPlan.COACHING_SCHOOL,
            ],
            "export_pdf": [
                UserPlan.PRO,
                UserPlan.ENTERPRISE,
                UserPlan.COACHING_SCHOOL,
            ],
            "export_srt": [UserPlan.ENTERPRISE, UserPlan.COACHING_SCHOOL],
            "priority_support": [
                UserPlan.PRO,
                UserPlan.ENTERPRISE,
                UserPlan.COACHING_SCHOOL,
            ],
            "api_access": [UserPlan.ENTERPRISE, UserPlan.COACHING_SCHOOL],
        }
        return self.plan in feature_access.get(feature, [])

    def update_usage_stats(self) -> None:
        """Update usage statistics from related records."""
        # Update session count
        self.session_count = self.get_sessions_count()

        # Update usage minutes from usage logs
        self.usage_minutes = self.get_total_usage_minutes()

        # Update timestamp
        self.updated_at = datetime.utcnow()

    def reset_monthly_usage(self) -> None:
        """Reset monthly usage counters (called by billing cycle)."""
        self.usage_minutes = 0
        self.session_count = 0
        self.updated_at = datetime.utcnow()

    def mark_active(self) -> None:
        """Update last active timestamp."""
        self.last_active_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def __repr__(self):
        """String representation of the UserModel."""
        return f"<UserModel(id={self.id}, email={self.email}, plan={self.plan.value if self.plan else 'None'})>"
