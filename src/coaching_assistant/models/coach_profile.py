"""Coach profile model for coach's public information."""

import enum
import json

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class CoachingLanguage(enum.Enum):
    """Languages that coach can provide services in."""

    MANDARIN = "mandarin"
    ENGLISH = "english"
    CANTONESE = "cantonese"
    JAPANESE = "japanese"
    KOREAN = "korean"
    SPANISH = "spanish"
    FRENCH = "french"
    GERMAN = "german"


class CommunicationTool(enum.Enum):
    """Communication tools available."""

    LINE = "line"
    ZOOM = "zoom"
    GOOGLE_MEET = "google_meet"
    MS_TEAMS = "ms_teams"
    SKYPE = "skype"
    WECHAT = "wechat"
    WHATSAPP = "whatsapp"


class CoachExperience(enum.Enum):
    """Coach experience levels."""

    BEGINNER = "beginner"  # 0-1 years
    INTERMEDIATE = "intermediate"  # 1-3 years
    ADVANCED = "advanced"  # 3-5 years
    EXPERT = "expert"  # 5+ years


class CoachingPlanType(enum.Enum):
    """Types of coaching plans."""

    SINGLE_SESSION = "single_session"
    PACKAGE = "package"
    GROUP = "group"
    WORKSHOP = "workshop"
    CUSTOM = "custom"


# Association tables for many-to-many relationships
coach_languages = Table(
    "coach_languages",
    BaseModel.metadata,
    Column(
        "coach_profile_id",
        UUID(as_uuid=True),
        ForeignKey("coach_profile.id"),
        primary_key=True,
    ),
    Column("language", String(50), primary_key=True),
)

coach_communication_tools = Table(
    "coach_communication_tools",
    BaseModel.metadata,
    Column(
        "coach_profile_id",
        UUID(as_uuid=True),
        ForeignKey("coach_profile.id"),
        primary_key=True,
    ),
    Column("tool", String(50), primary_key=True),
)


class CoachProfile(BaseModel):
    """Coach profile containing public information."""

    # Foreign key to User
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id"), unique=True, nullable=False
    )

    # Basic public information
    display_name = Column(String(255), nullable=False)
    profile_photo_url = Column(Text)  # Can store base64 image data or URLs
    public_email = Column(String(255))
    phone_country_code = Column(String(10))
    phone_number = Column(String(50))
    country = Column(String(100))
    city = Column(String(100))
    timezone = Column(String(50))

    # Language settings (stored as JSON array for simplicity, or use
    # association table)
    coaching_languages = Column(Text)  # JSON array of language codes

    # Communication tools (stored as JSON object)
    communication_tools = Column(Text)  # JSON object with tool settings
    line_id = Column(String(100))

    # Professional information
    coach_experience = Column(
        String(50)
    )  # Using String instead of Enum for flexibility
    training_institution = Column(String(255))
    certifications = Column(Text)  # Can store multiple certifications as JSON array
    linkedin_url = Column(String(512))
    personal_website = Column(String(512))

    # Coach introduction
    bio = Column(Text)
    specialties = Column(Text)  # JSON array of specialties

    # Visibility settings
    is_public = Column(Boolean, default=False)

    # Relationship
    user = relationship("User", back_populates="coach_profile", uselist=False)
    coaching_plans = relationship(
        "CoachingPlan",
        back_populates="coach_profile",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self):
        return (
            f"<CoachProfile(display_name={self.display_name}, user_id={self.user_id})>"
        )

    def get_coaching_languages(self):
        """Get coaching languages as list."""
        if not self.coaching_languages:
            return []
        try:
            return json.loads(self.coaching_languages)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_coaching_languages(self, languages):
        """Set coaching languages from list."""
        self.coaching_languages = json.dumps(languages)

    def get_communication_tools(self):
        """Get communication tools as dict."""
        if not self.communication_tools:
            return {}
        try:
            return json.loads(self.communication_tools)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_communication_tools(self, tools):
        """Set communication tools from dict."""
        self.communication_tools = json.dumps(tools)

    def get_certifications(self):
        """Get certifications as list."""
        if not self.certifications:
            return []
        try:
            return json.loads(self.certifications)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_certifications(self, certs):
        """Set certifications from list."""
        self.certifications = json.dumps(certs)

    def get_specialties(self):
        """Get specialties as list."""
        if not self.specialties:
            return []
        try:
            return json.loads(self.specialties)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_specialties(self, specs):
        """Set specialties from list."""
        self.specialties = json.dumps(specs)


class CoachingPlan(BaseModel):
    """Coaching plan/package offered by coach."""

    # Foreign key to CoachProfile
    coach_profile_id = Column(
        UUID(as_uuid=True), ForeignKey("coach_profile.id"), nullable=False
    )

    # Plan details
    plan_type = Column(String(50), nullable=False)  # Using String for flexibility
    title = Column(String(255), nullable=False)
    description = Column(Text)

    # Pricing
    duration_minutes = Column(Integer)  # Duration per session
    number_of_sessions = Column(Integer, default=1)  # Number of sessions in package
    price = Column(Float, nullable=False)
    currency = Column(String(10), default="NTD")

    # Availability
    is_active = Column(Boolean, default=True)
    max_participants = Column(Integer, default=1)  # For group sessions

    # Additional settings
    booking_notice_hours = Column(
        Integer, default=24
    )  # Hours notice required for booking
    cancellation_notice_hours = Column(Integer, default=24)

    # Relationship
    coach_profile = relationship("CoachProfile", back_populates="coaching_plans")

    def __repr__(self):
        return f"<CoachingPlan(title={self.title}, type={self.plan_type}, price={self.price})>"

    @property
    def price_per_session(self):
        """Calculate price per session."""
        if self.number_of_sessions and self.number_of_sessions > 0:
            return self.price / self.number_of_sessions
        return self.price

    @property
    def total_duration_minutes(self):
        """Calculate total duration for package."""
        if (
            self.duration_minutes
            and self.number_of_sessions
            and self.number_of_sessions > 0
        ):
            return self.duration_minutes * self.number_of_sessions
        elif self.number_of_sessions == 0:
            return 0  # No sessions = no total duration
        return self.duration_minutes or 0
