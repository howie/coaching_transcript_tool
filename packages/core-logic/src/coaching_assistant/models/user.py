"""User model and related enums."""

import enum
import json
from sqlalchemy import Column, String, Integer, Enum, Text
from sqlalchemy.orm import relationship
from .base import BaseModel


class UserPlan(enum.Enum):
    """User subscription plans."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class User(BaseModel):
    """User model for authenticated users."""
    
    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable for SSO users
    
    # Profile fields
    name = Column(String(255), nullable=False)
    avatar_url = Column(String(512))
    
    # SSO fields
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    
    # Subscription and usage
    plan = Column(Enum(UserPlan), default=UserPlan.FREE, nullable=False)
    usage_minutes = Column(Integer, default=0, nullable=False)
    
    # User preferences (stored as JSON)
    preferences = Column(Text, nullable=True)
    
    # Relationships
    sessions = relationship(
        "Session", 
        back_populates="user", 
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    clients = relationship(
        "Client", 
        back_populates="coach", 
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    coaching_sessions = relationship(
        "CoachingSession", 
        back_populates="coach", 
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
    
    def get_preferences(self):
        """Get user preferences as dict."""
        if not self.preferences:
            return {
                'language': 'system'
            }
        try:
            return json.loads(self.preferences)
        except (json.JSONDecodeError, TypeError):
            return {
                'language': 'system'
            }
    
    def set_preferences(self, preferences_dict):
        """Set user preferences from dict."""
        current_prefs = self.get_preferences()
        current_prefs.update(preferences_dict)
        self.preferences = json.dumps(current_prefs)
    
    @property
    def auth_provider(self):
        """Determine authentication provider."""
        if self.google_id:
            return 'google'
        return 'email'
    
    @property
    def google_connected(self):
        """Check if Google account is connected."""
        return bool(self.google_id)
