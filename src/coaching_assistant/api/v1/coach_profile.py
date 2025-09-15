"""Coach Profile API endpoints - Synchronous version."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, UUID4
from datetime import datetime

from ...core.database import get_db
from ...models import User, CoachProfile, CoachingPlan
from .auth import get_current_user_dependency


router = APIRouter(tags=["coach-profile"])


# Pydantic models for request/response
class CommunicationToolsModel(BaseModel):
    """Communication tools configuration."""

    line: bool = False
    zoom: bool = False
    google_meet: bool = False
    ms_teams: bool = False
    skype: bool = False
    wechat: bool = False
    whatsapp: bool = False


class CoachProfileCreate(BaseModel):
    """Create coach profile request."""

    display_name: str = Field(..., min_length=1, max_length=255)
    profile_photo_url: Optional[str] = None
    public_email: Optional[str] = None
    phone_country_code: Optional[str] = None
    phone_number: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None
    coaching_languages: List[str] = Field(default_factory=list)
    communication_tools: CommunicationToolsModel = Field(
        default_factory=CommunicationToolsModel
    )
    line_id: Optional[str] = None
    coach_experience: Optional[str] = None
    training_institution: Optional[str] = None
    certifications: List[str] = Field(default_factory=list)
    linkedin_url: Optional[str] = None
    personal_website: Optional[str] = None
    bio: Optional[str] = None
    specialties: List[str] = Field(default_factory=list)
    is_public: bool = False


class CoachProfileUpdate(BaseModel):
    """Update coach profile request."""

    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    profile_photo_url: Optional[str] = None
    public_email: Optional[str] = None
    phone_country_code: Optional[str] = None
    phone_number: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None
    coaching_languages: Optional[List[str]] = None
    communication_tools: Optional[CommunicationToolsModel] = None
    line_id: Optional[str] = None
    coach_experience: Optional[str] = None
    training_institution: Optional[str] = None
    certifications: Optional[List[str]] = None
    linkedin_url: Optional[str] = None
    personal_website: Optional[str] = None
    bio: Optional[str] = None
    specialties: Optional[List[str]] = None
    is_public: Optional[bool] = None


class CoachProfileResponse(BaseModel):
    """Coach profile response."""

    id: UUID4
    user_id: UUID4
    display_name: str
    profile_photo_url: Optional[str]
    public_email: Optional[str]
    phone_country_code: Optional[str]
    phone_number: Optional[str]
    country: Optional[str]
    city: Optional[str]
    timezone: Optional[str]
    coaching_languages: List[str]
    communication_tools: dict
    line_id: Optional[str]
    coach_experience: Optional[str]
    training_institution: Optional[str]
    certifications: List[str]
    linkedin_url: Optional[str]
    personal_website: Optional[str]
    bio: Optional[str]
    specialties: List[str]
    is_public: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CoachingPlanCreate(BaseModel):
    """Create coaching plan request."""

    plan_type: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=480)
    number_of_sessions: int = Field(1, ge=1)
    price: float = Field(..., ge=0)
    currency: str = Field("NTD", max_length=10)
    is_active: bool = True
    max_participants: int = Field(1, ge=1)
    booking_notice_hours: int = Field(24, ge=0)
    cancellation_notice_hours: int = Field(24, ge=0)


class CoachingPlanUpdate(BaseModel):
    """Update coaching plan request."""

    plan_type: Optional[str] = Field(None, min_length=1, max_length=50)
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=480)
    number_of_sessions: Optional[int] = Field(None, ge=1)
    price: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=10)
    is_active: Optional[bool] = None
    max_participants: Optional[int] = Field(None, ge=1)
    booking_notice_hours: Optional[int] = Field(None, ge=0)
    cancellation_notice_hours: Optional[int] = Field(None, ge=0)


class CoachingPlanResponse(BaseModel):
    """Coaching plan response."""

    id: UUID4
    coach_profile_id: UUID4
    plan_type: str
    title: str
    description: Optional[str]
    duration_minutes: Optional[int]
    number_of_sessions: int
    price: float
    currency: str
    is_active: bool
    max_participants: int
    booking_notice_hours: int
    cancellation_notice_hours: int
    price_per_session: float
    total_duration_minutes: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


def _profile_to_response(profile: CoachProfile) -> CoachProfileResponse:
    """Convert CoachProfile model to response."""
    return CoachProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        display_name=profile.display_name,
        profile_photo_url=profile.profile_photo_url,
        public_email=profile.public_email,
        phone_country_code=profile.phone_country_code,
        phone_number=profile.phone_number,
        country=profile.country,
        city=profile.city,
        timezone=profile.timezone,
        coaching_languages=profile.get_coaching_languages(),
        communication_tools=profile.get_communication_tools(),
        line_id=profile.line_id,
        coach_experience=profile.coach_experience,
        training_institution=profile.training_institution,
        certifications=profile.get_certifications(),
        linkedin_url=profile.linkedin_url,
        personal_website=profile.personal_website,
        bio=profile.bio,
        specialties=profile.get_specialties(),
        is_public=profile.is_public,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def _plan_to_response(plan: CoachingPlan) -> CoachingPlanResponse:
    """Convert CoachingPlan model to response."""
    return CoachingPlanResponse(
        id=plan.id,
        coach_profile_id=plan.coach_profile_id,
        plan_type=plan.plan_type,
        title=plan.title,
        description=plan.description,
        duration_minutes=plan.duration_minutes,
        number_of_sessions=plan.number_of_sessions,
        price=plan.price,
        currency=plan.currency,
        is_active=plan.is_active,
        max_participants=plan.max_participants,
        booking_notice_hours=plan.booking_notice_hours,
        cancellation_notice_hours=plan.cancellation_notice_hours,
        price_per_session=plan.price_per_session,
        total_duration_minutes=plan.total_duration_minutes,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


# Coach Profile endpoints
@router.get("/", response_model=Optional[CoachProfileResponse])
def get_coach_profile(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Get current user's coach profile."""
    profile = (
        db.query(CoachProfile)
        .filter(CoachProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        return None

    return _profile_to_response(profile)


@router.post(
    "/",
    response_model=CoachProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_coach_profile(
    profile_data: CoachProfileCreate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Create a coach profile for the current user."""
    # Check if profile already exists
    existing_profile = (
        db.query(CoachProfile)
        .filter(CoachProfile.user_id == current_user.id)
        .first()
    )

    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coach profile already exists for this user",
        )

    # Create new profile
    profile = CoachProfile(
        user_id=current_user.id,
        display_name=profile_data.display_name,
        profile_photo_url=profile_data.profile_photo_url,
        public_email=profile_data.public_email,
        phone_country_code=profile_data.phone_country_code,
        phone_number=profile_data.phone_number,
        country=profile_data.country,
        city=profile_data.city,
        timezone=profile_data.timezone,
        line_id=profile_data.line_id,
        coach_experience=profile_data.coach_experience,
        training_institution=profile_data.training_institution,
        linkedin_url=profile_data.linkedin_url,
        personal_website=profile_data.personal_website,
        bio=profile_data.bio,
        is_public=profile_data.is_public,
    )

    # Set JSON fields
    profile.set_coaching_languages(profile_data.coaching_languages)
    profile.set_communication_tools(
        profile_data.communication_tools.model_dump()
    )
    profile.set_certifications(profile_data.certifications)
    profile.set_specialties(profile_data.specialties)

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return _profile_to_response(profile)


@router.put("/", response_model=CoachProfileResponse)
def update_coach_profile(
    profile_data: CoachProfileUpdate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Update the current user's coach profile."""
    profile = (
        db.query(CoachProfile)
        .filter(CoachProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coach profile not found",
        )

    # Update fields
    update_data = profile_data.model_dump(exclude_unset=True)

    # Handle JSON fields separately
    if "coaching_languages" in update_data:
        profile.set_coaching_languages(update_data.pop("coaching_languages"))
    if "communication_tools" in update_data:
        tools = update_data.pop("communication_tools")
        if hasattr(tools, "model_dump"):
            profile.set_communication_tools(tools.model_dump())
        else:
            profile.set_communication_tools(tools)
    if "certifications" in update_data:
        profile.set_certifications(update_data.pop("certifications"))
    if "specialties" in update_data:
        profile.set_specialties(update_data.pop("specialties"))

    # Update remaining fields
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    return _profile_to_response(profile)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_coach_profile(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Delete the current user's coach profile."""
    profile = (
        db.query(CoachProfile)
        .filter(CoachProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coach profile not found",
        )

    db.delete(profile)
    db.commit()


# Coaching Plan endpoints
@router.get("/plans", response_model=List[CoachingPlanResponse])
def get_coaching_plans(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Get all coaching plans for the current user's profile."""
    # Get coach profile
    profile = (
        db.query(CoachProfile)
        .filter(CoachProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coach profile not found",
        )

    # Get plans
    plans = (
        db.query(CoachingPlan)
        .filter(CoachingPlan.coach_profile_id == profile.id)
        .all()
    )

    return [_plan_to_response(plan) for plan in plans]


@router.post(
    "/plans",
    response_model=CoachingPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_coaching_plan(
    plan_data: CoachingPlanCreate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Create a new coaching plan."""
    # Get coach profile
    profile = (
        db.query(CoachProfile)
        .filter(CoachProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coach profile not found. Please create a coach profile first.",
        )

    # Create plan
    plan = CoachingPlan(
        coach_profile_id=profile.id,
        plan_type=plan_data.plan_type,
        title=plan_data.title,
        description=plan_data.description,
        duration_minutes=plan_data.duration_minutes,
        number_of_sessions=plan_data.number_of_sessions,
        price=plan_data.price,
        currency=plan_data.currency,
        is_active=plan_data.is_active,
        max_participants=plan_data.max_participants,
        booking_notice_hours=plan_data.booking_notice_hours,
        cancellation_notice_hours=plan_data.cancellation_notice_hours,
    )

    db.add(plan)
    db.commit()
    db.refresh(plan)

    return _plan_to_response(plan)


@router.put("/plans/{plan_id}", response_model=CoachingPlanResponse)
def update_coaching_plan(
    plan_id: UUID4,
    plan_data: CoachingPlanUpdate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Update a coaching plan."""
    # Get coach profile
    profile = (
        db.query(CoachProfile)
        .filter(CoachProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coach profile not found",
        )

    # Get plan
    plan = (
        db.query(CoachingPlan)
        .filter(
            CoachingPlan.id == plan_id,
            CoachingPlan.coach_profile_id == profile.id,
        )
        .first()
    )

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coaching plan not found",
        )

    # Update fields
    update_data = plan_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)

    db.commit()
    db.refresh(plan)

    return _plan_to_response(plan)


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_coaching_plan(
    plan_id: UUID4,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Delete a coaching plan."""
    # Get coach profile
    profile = (
        db.query(CoachProfile)
        .filter(CoachProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coach profile not found",
        )

    # Get plan
    plan = (
        db.query(CoachingPlan)
        .filter(
            CoachingPlan.id == plan_id,
            CoachingPlan.coach_profile_id == profile.id,
        )
        .first()
    )

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coaching plan not found",
        )

    db.delete(plan)
    db.commit()
