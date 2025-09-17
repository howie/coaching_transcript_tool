"""User domain model with business rules."""

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


class UserPlan(enum.Enum):
    """User subscription plans."""

    FREE = "free"
    STUDENT = "student"
    PRO = "pro"
    ENTERPRISE = "enterprise"  # Deprecated, kept for backward compatibility
    COACHING_SCHOOL = "coaching_school"  # Replaces ENTERPRISE


class UserRole(enum.Enum):
    """User roles for access control."""

    USER = "user"  # Regular user
    STAFF = "staff"  # Support staff (read-only admin)
    ADMIN = "admin"  # Full admin (read/write)
    SUPER_ADMIN = "super_admin"  # System admin (manage other admins)


@dataclass
class PlanLimits:
    """Plan-specific limits and features."""

    monthly_minutes: int
    max_file_size_mb: int
    max_sessions_per_month: int
    ai_analysis_enabled: bool
    export_formats: list[str]

    @classmethod
    def for_plan(cls, plan: UserPlan) -> "PlanLimits":
        """Get limits for a specific plan."""
        limits_map = {
            UserPlan.FREE: cls(
                monthly_minutes=120,
                max_file_size_mb=60,
                max_sessions_per_month=10,
                ai_analysis_enabled=False,
                export_formats=["txt"]
            ),
            UserPlan.STUDENT: cls(
                monthly_minutes=300,
                max_file_size_mb=100,
                max_sessions_per_month=20,
                ai_analysis_enabled=True,
                export_formats=["txt", "docx"]
            ),
            UserPlan.PRO: cls(
                monthly_minutes=600,
                max_file_size_mb=200,
                max_sessions_per_month=50,
                ai_analysis_enabled=True,
                export_formats=["txt", "docx", "pdf"]
            ),
            UserPlan.ENTERPRISE: cls(
                monthly_minutes=1200,
                max_file_size_mb=500,
                max_sessions_per_month=100,
                ai_analysis_enabled=True,
                export_formats=["txt", "docx", "pdf", "srt"]
            ),
            UserPlan.COACHING_SCHOOL: cls(
                monthly_minutes=2000,
                max_file_size_mb=500,
                max_sessions_per_month=200,
                ai_analysis_enabled=True,
                export_formats=["txt", "docx", "pdf", "srt"]
            ),
        }
        return limits_map.get(plan, limits_map[UserPlan.FREE])


@dataclass
class User:
    """Pure domain model for User entity with business rules."""

    # Core identity
    id: Optional[UUID] = None
    email: str = ""
    name: str = ""

    # Authentication
    hashed_password: Optional[str] = None
    avatar_url: Optional[str] = None

    # Plan and permissions
    plan: UserPlan = UserPlan.FREE
    role: UserRole = UserRole.USER

    # Usage tracking
    usage_minutes: int = 0
    session_count: int = 0
    current_month_start: Optional[datetime] = None  # Billing period start

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_active_at: Optional[datetime] = None

    # Subscription info
    stripe_customer_id: Optional[str] = None
    subscription_status: Optional[str] = None

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.id is None:
            self.id = uuid4()
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    # Business Rules

    def can_create_session(self) -> bool:
        """Business rule: Check if user can create new session."""
        limits = self.get_plan_limits()
        return (
            self.usage_minutes < limits.monthly_minutes and
            self.session_count < limits.max_sessions_per_month
        )

    def can_upload_file(self, file_size_mb: float) -> bool:
        """Business rule: Check if user can upload file of given size."""
        limits = self.get_plan_limits()
        return file_size_mb <= limits.max_file_size_mb

    def can_use_ai_analysis(self) -> bool:
        """Business rule: Check if user can use AI analysis features."""
        limits = self.get_plan_limits()
        return limits.ai_analysis_enabled

    def can_export_format(self, format_type: str) -> bool:
        """Business rule: Check if user can export in given format."""
        limits = self.get_plan_limits()
        return format_type.lower() in [fmt.lower() for fmt in limits.export_formats]

    def get_plan_limits(self) -> PlanLimits:
        """Business rule: Get plan-specific limits."""
        return PlanLimits.for_plan(self.plan)

    def upgrade_plan(self, new_plan: UserPlan) -> None:
        """Business rule: Upgrade user plan with validation."""
        plan_values = {
            UserPlan.FREE: 0,
            UserPlan.STUDENT: 1,
            UserPlan.PRO: 2,
            UserPlan.ENTERPRISE: 3,
            UserPlan.COACHING_SCHOOL: 4,
        }

        current_value = plan_values.get(self.plan, 0)
        new_value = plan_values.get(new_plan, 0)

        if new_value <= current_value:
            raise ValueError(f"Cannot downgrade from {self.plan.value} to {new_plan.value}")

        self.plan = new_plan
        self.updated_at = datetime.utcnow()

    def add_usage_minutes(self, minutes: int) -> None:
        """Business rule: Add usage minutes with validation."""
        if minutes < 0:
            raise ValueError("Cannot add negative minutes")

        self.usage_minutes += minutes
        self.updated_at = datetime.utcnow()

    def increment_session_count(self) -> None:
        """Business rule: Increment session count."""
        self.session_count += 1
        self.updated_at = datetime.utcnow()

    def reset_monthly_usage(self) -> None:
        """Business rule: Reset monthly counters (called by billing cycle)."""
        self.usage_minutes = 0
        self.session_count = 0
        self.updated_at = datetime.utcnow()

    def update_last_active(self) -> None:
        """Business rule: Update last active timestamp."""
        self.last_active_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def has_permission(self, required_role: UserRole) -> bool:
        """Business rule: Check if user has required permission level."""
        role_levels = {
            UserRole.USER: 0,
            UserRole.STAFF: 1,
            UserRole.ADMIN: 2,
            UserRole.SUPER_ADMIN: 3,
        }

        current_level = role_levels.get(self.role, 0)
        required_level = role_levels.get(required_role, 0)

        return current_level >= required_level

    def is_premium_user(self) -> bool:
        """Business rule: Check if user has premium features."""
        return self.plan in [UserPlan.PRO, UserPlan.ENTERPRISE, UserPlan.COACHING_SCHOOL]

    def is_active_subscription(self) -> bool:
        """Business rule: Check if user has active subscription."""
        return self.subscription_status in ["active", "trialing"]

    def get_remaining_minutes(self) -> int:
        """Business rule: Calculate remaining minutes for current month."""
        limits = self.get_plan_limits()
        remaining = limits.monthly_minutes - self.usage_minutes
        return max(0, remaining)

    def get_remaining_sessions(self) -> int:
        """Business rule: Calculate remaining sessions for current month."""
        limits = self.get_plan_limits()
        remaining = limits.max_sessions_per_month - self.session_count
        return max(0, remaining)

    def get_usage_percentage(self) -> float:
        """Business rule: Calculate usage percentage for current month."""
        limits = self.get_plan_limits()
        if limits.monthly_minutes == 0:
            return 0.0

        percentage = (self.usage_minutes / limits.monthly_minutes) * 100
        return min(100.0, percentage)