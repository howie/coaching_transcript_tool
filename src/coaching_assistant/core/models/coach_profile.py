"""Coach profile domain model for Clean Architecture."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID


class CoachingLanguage(Enum):
    """Languages that coach can provide services in."""
    MANDARIN = "mandarin"
    ENGLISH = "english"
    CANTONESE = "cantonese"
    JAPANESE = "japanese"
    KOREAN = "korean"
    SPANISH = "spanish"
    FRENCH = "french"
    GERMAN = "german"


class CommunicationTool(Enum):
    """Communication tools available."""
    LINE = "line"
    ZOOM = "zoom"
    GOOGLE_MEET = "google_meet"
    MS_TEAMS = "ms_teams"
    SKYPE = "skype"
    WECHAT = "wechat"
    WHATSAPP = "whatsapp"


class CoachExperience(Enum):
    """Coach experience levels."""
    BEGINNER = "beginner"  # 0-1 years
    INTERMEDIATE = "intermediate"  # 1-3 years
    ADVANCED = "advanced"  # 3-5 years
    EXPERT = "expert"  # 5+ years


@dataclass
class CoachProfile:
    """Domain model for coach profiles."""

    # Identifiers
    id: Optional[UUID] = None
    user_id: UUID = None

    # Basic info
    public_name: str = None
    bio: Optional[str] = None
    location: Optional[str] = None
    timezone: str = "Asia/Taipei"

    # Professional info
    experience_level: CoachExperience = CoachExperience.BEGINNER
    specializations: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    languages: List[CoachingLanguage] = field(default_factory=list)
    communication_tools: List[CommunicationTool] = field(default_factory=list)

    # Rates and availability
    hourly_rate_min: Optional[int] = None
    hourly_rate_max: Optional[int] = None
    currency: str = "TWD"
    is_accepting_clients: bool = True

    # Profile visibility
    is_public: bool = False
    profile_photo_url: Optional[str] = None

    # Contact info
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website_url: Optional[str] = None

    # Audit fields
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def rate_range_display(self) -> str:
        """Get formatted rate range for display."""
        if self.hourly_rate_min and self.hourly_rate_max:
            return f"{self.currency} {self.hourly_rate_min}-{self.hourly_rate_max}/hr"
        elif self.hourly_rate_min:
            return f"{self.currency} {self.hourly_rate_min}+/hr"
        return "Rate negotiable"

    def __repr__(self):
        return f"<CoachProfile(name={self.public_name}, user_id={self.user_id})>"