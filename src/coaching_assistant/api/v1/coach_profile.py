"""Coach Profile API endpoints - Synchronous version."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import UUID4, BaseModel, ConfigDict, Field

from ...core.models.coach_profile import (
    CoachExperience,
    CoachingLanguage,
    CoachProfile,
    CommunicationTool,
)
from ...core.models.coaching_plan import CoachingPlan
from ...core.services.coach_profile_management_use_case import (
    CoachProfileManagementUseCase,
)
from ...models import User
from .auth import get_current_user_dependency
from .dependencies import get_coach_profile_management_use_case

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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


def _profile_to_response(profile: CoachProfile) -> CoachProfileResponse:
    """Convert CoachProfile domain model to response."""
    # Parse location back to city/country
    city = None
    country = None
    if profile.location:
        parts = profile.location.split(", ")
        if len(parts) >= 2:
            city = parts[0]
            country = parts[1]
        else:
            city = profile.location

    # Parse phone back to country code/number
    phone_country_code = None
    phone_number = None
    if profile.contact_phone:
        if profile.contact_phone.startswith("+"):
            phone_country_code = profile.contact_phone[:3]
            phone_number = profile.contact_phone[3:]
        else:
            phone_number = profile.contact_phone

    # Convert communication tools to dict
    communication_tools = {tool.value: True for tool in profile.communication_tools}

    return CoachProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        display_name=profile.public_name,
        profile_photo_url=profile.profile_photo_url,
        public_email=profile.contact_email,
        phone_country_code=phone_country_code,
        phone_number=phone_number,
        country=country,
        city=city,
        timezone=profile.timezone,
        coaching_languages=[lang.value for lang in profile.languages],
        communication_tools=communication_tools,
        line_id=None,  # Not in domain model - legacy field
        coach_experience=(
            profile.experience_level.value if profile.experience_level else None
        ),
        training_institution=None,  # Not in domain model - legacy field
        certifications=profile.certifications,
        linkedin_url=None,  # Not in domain model - legacy field
        personal_website=profile.website_url,
        bio=profile.bio,
        specialties=profile.specializations,
        is_public=profile.is_public,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def _plan_to_response(plan: CoachingPlan) -> CoachingPlanResponse:
    """Convert CoachingPlan domain model to response."""
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


def _create_request_to_domain(
    profile_data: CoachProfileCreate,
) -> CoachProfile:
    """Convert CoachProfileCreate request to domain model."""
    # Parse languages
    languages = []
    for lang_str in profile_data.coaching_languages:
        try:
            languages.append(CoachingLanguage(lang_str))
        except ValueError:
            continue

    # Parse communication tools
    communication_tools = []
    tools_dict = profile_data.communication_tools.model_dump()
    for tool_name, enabled in tools_dict.items():
        if enabled:
            try:
                communication_tools.append(CommunicationTool(tool_name))
            except ValueError:
                continue

    # Parse experience level
    experience_level = CoachExperience.BEGINNER
    if profile_data.coach_experience:
        try:
            experience_level = CoachExperience(profile_data.coach_experience)
        except ValueError:
            pass

    # Combine location
    location = None
    if profile_data.city and profile_data.country:
        location = f"{profile_data.city}, {profile_data.country}"
    elif profile_data.city:
        location = profile_data.city

    # Combine phone
    contact_phone = None
    if profile_data.phone_country_code and profile_data.phone_number:
        contact_phone = f"{profile_data.phone_country_code}{profile_data.phone_number}"
    elif profile_data.phone_number:
        contact_phone = profile_data.phone_number

    return CoachProfile(
        public_name=profile_data.display_name,
        bio=profile_data.bio,
        location=location,
        timezone=profile_data.timezone or "Asia/Taipei",
        experience_level=experience_level,
        specializations=profile_data.specialties,
        certifications=profile_data.certifications,
        languages=languages,
        communication_tools=communication_tools,
        is_public=profile_data.is_public,
        profile_photo_url=profile_data.profile_photo_url,
        contact_email=profile_data.public_email,
        contact_phone=contact_phone,
        website_url=profile_data.personal_website,
    )


def _update_request_to_domain(
    profile_data: CoachProfileUpdate, existing_profile: CoachProfile
) -> CoachProfile:
    """Convert CoachProfileUpdate request to domain model."""
    # Start with existing profile
    updated_profile = CoachProfile(
        id=existing_profile.id,
        user_id=existing_profile.user_id,
        public_name=existing_profile.public_name,
        bio=existing_profile.bio,
        location=existing_profile.location,
        timezone=existing_profile.timezone,
        experience_level=existing_profile.experience_level,
        specializations=existing_profile.specializations,
        certifications=existing_profile.certifications,
        languages=existing_profile.languages,
        communication_tools=existing_profile.communication_tools,
        is_public=existing_profile.is_public,
        profile_photo_url=existing_profile.profile_photo_url,
        contact_email=existing_profile.contact_email,
        contact_phone=existing_profile.contact_phone,
        website_url=existing_profile.website_url,
        created_at=existing_profile.created_at,
        updated_at=existing_profile.updated_at,
    )

    # Apply updates
    if profile_data.display_name is not None:
        updated_profile.public_name = profile_data.display_name
    if profile_data.bio is not None:
        updated_profile.bio = profile_data.bio
    if profile_data.timezone is not None:
        updated_profile.timezone = profile_data.timezone
    if profile_data.is_public is not None:
        updated_profile.is_public = profile_data.is_public
    if profile_data.profile_photo_url is not None:
        updated_profile.profile_photo_url = profile_data.profile_photo_url
    if profile_data.public_email is not None:
        updated_profile.contact_email = profile_data.public_email
    if profile_data.personal_website is not None:
        updated_profile.website_url = profile_data.personal_website

    # Update location
    if profile_data.city is not None or profile_data.country is not None:
        city = profile_data.city
        country = profile_data.country
        if city and country:
            updated_profile.location = f"{city}, {country}"
        elif city:
            updated_profile.location = city
        else:
            updated_profile.location = None

    # Update phone
    if (
        profile_data.phone_country_code is not None
        or profile_data.phone_number is not None
    ):
        country_code = profile_data.phone_country_code
        number = profile_data.phone_number
        if country_code and number:
            updated_profile.contact_phone = f"{country_code}{number}"
        elif number:
            updated_profile.contact_phone = number
        else:
            updated_profile.contact_phone = None

    # Update languages
    if profile_data.coaching_languages is not None:
        languages = []
        for lang_str in profile_data.coaching_languages:
            try:
                languages.append(CoachingLanguage(lang_str))
            except ValueError:
                continue
        updated_profile.languages = languages

    # Update communication tools
    if profile_data.communication_tools is not None:
        communication_tools = []
        tools_dict = profile_data.communication_tools.model_dump()
        for tool_name, enabled in tools_dict.items():
            if enabled:
                try:
                    communication_tools.append(CommunicationTool(tool_name))
                except ValueError:
                    continue
        updated_profile.communication_tools = communication_tools

    # Update experience level
    if profile_data.coach_experience is not None:
        try:
            updated_profile.experience_level = CoachExperience(
                profile_data.coach_experience
            )
        except ValueError:
            pass

    # Update certifications and specialties
    if profile_data.certifications is not None:
        updated_profile.certifications = profile_data.certifications
    if profile_data.specialties is not None:
        updated_profile.specializations = profile_data.specialties

    return updated_profile


def _plan_create_request_to_domain(
    plan_data: CoachingPlanCreate,
) -> CoachingPlan:
    """Convert CoachingPlanCreate request to domain model."""
    return CoachingPlan(
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


def _plan_update_request_to_domain(
    plan_data: CoachingPlanUpdate, existing_plan: CoachingPlan
) -> CoachingPlan:
    """Convert CoachingPlanUpdate request to domain model."""
    # Start with existing plan
    updated_plan = CoachingPlan(
        id=existing_plan.id,
        coach_profile_id=existing_plan.coach_profile_id,
        plan_type=existing_plan.plan_type,
        title=existing_plan.title,
        description=existing_plan.description,
        duration_minutes=existing_plan.duration_minutes,
        number_of_sessions=existing_plan.number_of_sessions,
        price=existing_plan.price,
        currency=existing_plan.currency,
        is_active=existing_plan.is_active,
        max_participants=existing_plan.max_participants,
        booking_notice_hours=existing_plan.booking_notice_hours,
        cancellation_notice_hours=existing_plan.cancellation_notice_hours,
        created_at=existing_plan.created_at,
        updated_at=existing_plan.updated_at,
    )

    # Apply updates
    update_data = plan_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(updated_plan, field):
            setattr(updated_plan, field, value)

    return updated_plan


# Coach Profile endpoints
@router.get("/", response_model=Optional[CoachProfileResponse])
def get_coach_profile(
    current_user: User = Depends(get_current_user_dependency),
    use_case: CoachProfileManagementUseCase = Depends(
        get_coach_profile_management_use_case
    ),
):
    """Get current user's coach profile."""
    try:
        profile = use_case.get_profile(current_user.id)

        if not profile:
            return None

        return _profile_to_response(profile)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/",
    response_model=CoachProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_coach_profile(
    profile_data: CoachProfileCreate,
    current_user: User = Depends(get_current_user_dependency),
    use_case: CoachProfileManagementUseCase = Depends(
        get_coach_profile_management_use_case
    ),
):
    """Create a coach profile for the current user."""
    try:
        domain_profile = _create_request_to_domain(profile_data)

        created_profile = use_case.create_profile(current_user.id, domain_profile)
        return _profile_to_response(created_profile)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/", response_model=CoachProfileResponse)
def update_coach_profile(
    profile_data: CoachProfileUpdate,
    current_user: User = Depends(get_current_user_dependency),
    use_case: CoachProfileManagementUseCase = Depends(
        get_coach_profile_management_use_case
    ),
):
    """Update the current user's coach profile."""
    try:
        # Get existing profile
        existing_profile = use_case.get_profile(current_user.id)
        if not existing_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Coach profile not found",
            )

        # Convert update request to domain model
        domain_profile = _update_request_to_domain(profile_data, existing_profile)

        # Update profile
        updated_profile = use_case.update_profile(current_user.id, domain_profile)
        return _profile_to_response(updated_profile)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_coach_profile(
    current_user: User = Depends(get_current_user_dependency),
    use_case: CoachProfileManagementUseCase = Depends(
        get_coach_profile_management_use_case
    ),
):
    """Delete the current user's coach profile."""
    try:
        deleted = use_case.delete_profile(current_user.id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Coach profile not found",
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Coaching Plan endpoints
@router.get("/plans", response_model=List[CoachingPlanResponse])
def get_coaching_plans(
    current_user: User = Depends(get_current_user_dependency),
    use_case: CoachProfileManagementUseCase = Depends(
        get_coach_profile_management_use_case
    ),
):
    """Get all coaching plans for the current user's profile."""
    try:
        plans = use_case.get_coaching_plans(current_user.id)

        return [_plan_to_response(plan) for plan in plans]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/plans",
    response_model=CoachingPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_coaching_plan(
    plan_data: CoachingPlanCreate,
    current_user: User = Depends(get_current_user_dependency),
    use_case: CoachProfileManagementUseCase = Depends(
        get_coach_profile_management_use_case
    ),
):
    """Create a new coaching plan."""
    try:
        domain_plan = _plan_create_request_to_domain(plan_data)

        created_plan = use_case.create_plan(current_user.id, domain_plan)
        return _plan_to_response(created_plan)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/plans/{plan_id}", response_model=CoachingPlanResponse)
def update_coaching_plan(
    plan_id: UUID4,
    plan_data: CoachingPlanUpdate,
    current_user: User = Depends(get_current_user_dependency),
    use_case: CoachProfileManagementUseCase = Depends(
        get_coach_profile_management_use_case
    ),
):
    """Update a coaching plan."""
    try:
        # Get existing plan through use case to verify ownership
        existing_plans = use_case.get_coaching_plans(current_user.id)
        existing_plan = next((p for p in existing_plans if p.id == plan_id), None)

        if not existing_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Coaching plan not found",
            )

        # Convert update request to domain model
        domain_plan = _plan_update_request_to_domain(plan_data, existing_plan)

        # Update plan
        updated_plan = use_case.update_plan(current_user.id, plan_id, domain_plan)
        return _plan_to_response(updated_plan)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_coaching_plan(
    plan_id: UUID4,
    current_user: User = Depends(get_current_user_dependency),
    use_case: CoachProfileManagementUseCase = Depends(
        get_coach_profile_management_use_case
    ),
):
    """Delete a coaching plan."""
    try:
        deleted = use_case.delete_plan(current_user.id, plan_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Coaching plan not found",
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
