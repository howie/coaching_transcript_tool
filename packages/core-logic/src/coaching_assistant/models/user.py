"""User model and related enums."""

import enum
from sqlalchemy import Column, String, Integer, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel


class UserPlan(enum.Enum):
    """User subscription plans."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class User(BaseModel):
    """User model for Google OAuth authenticated users."""
    
    # Google OAuth fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    avatar_url = Column(String(512))
    google_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Subscription and usage
    plan = Column(Enum(UserPlan), default=UserPlan.FREE, nullable=False)
    usage_minutes = Column(Integer, default=0, nullable=False)
    
    # Relationships
    sessions = relationship(
        "Session", 
        back_populates="user", 
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def __repr__(self):
        return f"<User(email={self.email}, plan={self.plan.value})>"
    
    def is_usage_within_limit(self, additional_minutes: int = 0) -> bool:
        """Check if user's usage is within plan limits."""
        total_minutes = self.usage_minutes + additional_minutes
        
        limits = {
            UserPlan.FREE: 60,      # 1 hour per month
            UserPlan.PRO: 600,      # 10 hours per month  
            UserPlan.ENTERPRISE: float('inf')  # unlimited
        }
        
        return total_minutes <= limits.get(self.plan, 0)
    
    def can_create_session(self, estimated_duration_minutes: int) -> bool:
        """Check if user can create a new session."""
        return self.is_usage_within_limit(estimated_duration_minutes)
    
    def add_usage(self, minutes: int):
        """Add usage minutes to user's total."""
        self.usage_minutes += minutes
    
    def reset_monthly_usage(self):
        """Reset usage counter (called monthly)."""
        self.usage_minutes = 0
