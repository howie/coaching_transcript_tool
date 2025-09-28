"""SQLAlchemy implementation of CoachProfileRepoPort with domain model conversion.

This module provides the concrete implementation of coach profile repository
operations using SQLAlchemy ORM with proper domain ↔ ORM conversion,
following Clean Architecture principles.
"""

import json
from typing import List, Optional
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session as DBSession

from ....core.models.coach_profile import (
    CoachExperience,
    CoachingLanguage,
    CoachProfile,
    CommunicationTool,
)
from ....core.models.coaching_plan import CoachingPlan
from ....core.repositories.ports import CoachProfileRepoPort

# Using legacy models temporarily until ORM migration is complete
from ....models.coach_profile import CoachingPlan as CoachingPlanModel
from ....models.coach_profile import CoachProfile as CoachProfileModel


class SQLAlchemyCoachProfileRepository(CoachProfileRepoPort):
    """SQLAlchemy implementation of the CoachProfileRepoPort interface with domain conversion."""

    def __init__(self, session: DBSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session

    def get_by_user_id(self, user_id: UUID) -> Optional[CoachProfile]:
        """Get coach profile by user ID.

        Args:
            user_id: UUID of the user

        Returns:
            CoachProfile domain entity or None if not found
        """
        try:
            orm_profile = (
                self.session.query(CoachProfileModel)
                .filter(CoachProfileModel.user_id == user_id)
                .first()
            )
            return self._legacy_to_domain(orm_profile) if orm_profile else None
        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Database error retrieving coach profile for user {user_id}"
            ) from e

    def save(self, profile: CoachProfile) -> CoachProfile:
        """Save or update coach profile.

        Args:
            profile: CoachProfile domain entity to save

        Returns:
            Saved CoachProfile domain entity with updated fields
        """
        try:
            if profile.id:
                # Update existing profile
                orm_profile = self.session.get(CoachProfileModel, profile.id)
                if orm_profile:
                    self._update_orm_from_domain(orm_profile, profile)
                else:
                    # Profile ID exists but not found in DB - create new
                    orm_profile = self._domain_to_legacy(profile)
                    self.session.add(orm_profile)
            else:
                # Create new profile
                orm_profile = self._domain_to_legacy(profile)
                self.session.add(orm_profile)

            self.session.commit()
            self.session.refresh(orm_profile)
            return self._legacy_to_domain(orm_profile)

        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(
                f"Database error saving coach profile for user {profile.user_id}"
            ) from e

    def delete(self, user_id: UUID) -> bool:
        """Delete coach profile by user ID.

        Args:
            user_id: UUID of the user

        Returns:
            True if profile was deleted, False if not found
        """
        try:
            orm_profile = (
                self.session.query(CoachProfileModel)
                .filter(CoachProfileModel.user_id == user_id)
                .first()
            )

            if orm_profile:
                self.session.delete(orm_profile)
                self.session.commit()
                return True
            return False

        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(
                f"Database error deleting coach profile for user {user_id}"
            ) from e

    def get_all_verified_coaches(self) -> List[CoachProfile]:
        """Get all verified coach profiles.

        Returns:
            List of CoachProfile domain entities
        """
        try:
            orm_profiles = (
                self.session.query(CoachProfileModel)
                .filter(CoachProfileModel.is_public.is_(True))
                .all()
            )
            return [self._legacy_to_domain(orm_profile) for orm_profile in orm_profiles]
        except SQLAlchemyError as e:
            raise RuntimeError(
                "Database error retrieving verified coach profiles"
            ) from e

    def get_coaching_plans_by_profile_id(self, profile_id: UUID) -> List[CoachingPlan]:
        """Get all coaching plans for a profile.

        Args:
            profile_id: UUID of the coach profile

        Returns:
            List of CoachingPlan domain entities
        """
        try:
            orm_plans = (
                self.session.query(CoachingPlanModel)
                .filter(CoachingPlanModel.coach_profile_id == profile_id)
                .all()
            )
            return [self._plan_legacy_to_domain(orm_plan) for orm_plan in orm_plans]
        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Database error retrieving coaching plans for profile {profile_id}"
            ) from e

    def get_coaching_plan_by_id(self, plan_id: UUID) -> Optional[CoachingPlan]:
        """Get coaching plan by ID.

        Args:
            plan_id: UUID of the coaching plan

        Returns:
            CoachingPlan domain entity or None if not found
        """
        try:
            orm_plan = self.session.get(CoachingPlanModel, plan_id)
            return self._plan_legacy_to_domain(orm_plan) if orm_plan else None
        except SQLAlchemyError as e:
            raise RuntimeError(
                f"Database error retrieving coaching plan {plan_id}"
            ) from e

    def save_coaching_plan(self, plan: CoachingPlan) -> CoachingPlan:
        """Save or update coaching plan.

        Args:
            plan: CoachingPlan domain entity to save

        Returns:
            Saved CoachingPlan domain entity with updated fields
        """
        try:
            if plan.id:
                # Update existing plan
                orm_plan = self.session.get(CoachingPlanModel, plan.id)
                if orm_plan:
                    self._update_plan_orm_from_domain(orm_plan, plan)
                else:
                    # Plan ID exists but not found in DB - create new
                    orm_plan = self._plan_domain_to_legacy(plan)
                    self.session.add(orm_plan)
            else:
                # Create new plan
                orm_plan = self._plan_domain_to_legacy(plan)
                self.session.add(orm_plan)

            self.session.commit()
            self.session.refresh(orm_plan)
            return self._plan_legacy_to_domain(orm_plan)

        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(
                f"Database error saving coaching plan {plan.title}"
            ) from e

    def delete_coaching_plan(self, plan_id: UUID) -> bool:
        """Delete coaching plan by ID.

        Args:
            plan_id: UUID of the coaching plan

        Returns:
            True if plan was deleted, False if not found
        """
        try:
            orm_plan = self.session.get(CoachingPlanModel, plan_id)

            if orm_plan:
                self.session.delete(orm_plan)
                self.session.commit()
                return True
            return False

        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(
                f"Database error deleting coaching plan {plan_id}"
            ) from e

    def _legacy_to_domain(self, orm_profile: CoachProfileModel) -> CoachProfile:
        """Convert legacy ORM model to domain model.

        Args:
            orm_profile: Legacy CoachProfile ORM model

        Returns:
            CoachProfile domain model
        """
        # Parse languages from JSON
        languages = []
        try:
            if orm_profile.coaching_languages:
                lang_data = json.loads(orm_profile.coaching_languages)
                for lang_str in lang_data:
                    try:
                        languages.append(CoachingLanguage(lang_str))
                    except ValueError:
                        # Skip invalid language values
                        continue
        except (json.JSONDecodeError, TypeError):
            pass

        # Parse communication tools from JSON
        communication_tools = []
        try:
            if orm_profile.communication_tools:
                tools_data = json.loads(orm_profile.communication_tools)
                if isinstance(tools_data, dict):
                    for tool_name, enabled in tools_data.items():
                        if enabled:
                            try:
                                communication_tools.append(CommunicationTool(tool_name))
                            except ValueError:
                                # Skip invalid tool values
                                continue
        except (json.JSONDecodeError, TypeError):
            pass

        # Parse certifications from JSON
        certifications = []
        try:
            if orm_profile.certifications:
                certifications = json.loads(orm_profile.certifications)
        except (json.JSONDecodeError, TypeError):
            pass

        # Parse specializations from JSON
        specializations = []
        try:
            if orm_profile.specialties:
                specializations = json.loads(orm_profile.specialties)
        except (json.JSONDecodeError, TypeError):
            pass

        # Parse experience level
        experience_level = CoachExperience.BEGINNER
        if orm_profile.coach_experience:
            try:
                experience_level = CoachExperience(orm_profile.coach_experience)
            except ValueError:
                pass

        return CoachProfile(
            id=UUID(str(orm_profile.id)) if orm_profile.id else None,
            user_id=(UUID(str(orm_profile.user_id)) if orm_profile.user_id else None),
            public_name=orm_profile.display_name or "",
            bio=orm_profile.bio,
            location=(
                f"{orm_profile.city}, {orm_profile.country}"
                if orm_profile.city and orm_profile.country
                else None
            ),
            timezone=orm_profile.timezone or "Asia/Taipei",
            experience_level=experience_level,
            specializations=specializations,
            certifications=certifications,
            languages=languages,
            communication_tools=communication_tools,
            is_public=orm_profile.is_public or False,
            profile_photo_url=orm_profile.profile_photo_url,
            contact_email=orm_profile.public_email,
            contact_phone=(
                f"{orm_profile.phone_country_code}{orm_profile.phone_number}"
                if orm_profile.phone_country_code and orm_profile.phone_number
                else None
            ),
            website_url=orm_profile.personal_website,
            created_at=orm_profile.created_at,
            updated_at=orm_profile.updated_at,
        )

    def _domain_to_legacy(self, profile: CoachProfile) -> CoachProfileModel:
        """Convert domain model to legacy ORM model.

        Args:
            profile: CoachProfile domain model

        Returns:
            Legacy CoachProfile ORM model
        """
        orm_profile = CoachProfileModel(
            id=profile.id,
            user_id=profile.user_id,
            display_name=profile.public_name,
            bio=profile.bio,
            timezone=profile.timezone,
            coach_experience=(
                profile.experience_level.value
                if profile.experience_level
                else CoachExperience.BEGINNER.value
            ),
            is_public=profile.is_public,
            profile_photo_url=profile.profile_photo_url,
            public_email=profile.contact_email,
            personal_website=profile.website_url,
        )

        # Parse location into city and country
        if profile.location:
            parts = profile.location.split(", ")
            if len(parts) >= 2:
                orm_profile.city = parts[0]
                orm_profile.country = parts[1]
            else:
                orm_profile.city = profile.location

        # Parse phone into country code and number
        if profile.contact_phone:
            # Simple parsing - could be improved
            if profile.contact_phone.startswith("+"):
                orm_profile.phone_country_code = profile.contact_phone[:3]
                orm_profile.phone_number = profile.contact_phone[3:]
            else:
                orm_profile.phone_number = profile.contact_phone

        # Convert lists to JSON
        orm_profile.set_coaching_languages([lang.value for lang in profile.languages])
        orm_profile.set_certifications(profile.certifications)
        orm_profile.set_specialties(profile.specializations)

        # Convert communication tools to dict
        tools_dict = {tool.value: True for tool in profile.communication_tools}
        orm_profile.set_communication_tools(tools_dict)

        return orm_profile

    def _update_orm_from_domain(
        self, orm_profile: CoachProfileModel, profile: CoachProfile
    ):
        """Update existing ORM model from domain model.

        Args:
            orm_profile: Existing legacy CoachProfile ORM model
            profile: CoachProfile domain model with updates
        """
        orm_profile.display_name = profile.public_name
        orm_profile.bio = profile.bio
        orm_profile.timezone = profile.timezone
        orm_profile.coach_experience = (
            profile.experience_level.value
            if profile.experience_level
            else CoachExperience.BEGINNER.value
        )
        orm_profile.is_public = profile.is_public
        orm_profile.profile_photo_url = profile.profile_photo_url
        orm_profile.public_email = profile.contact_email
        orm_profile.personal_website = profile.website_url

        # Parse location into city and country
        if profile.location:
            parts = profile.location.split(", ")
            if len(parts) >= 2:
                orm_profile.city = parts[0]
                orm_profile.country = parts[1]
            else:
                orm_profile.city = profile.location

        # Parse phone into country code and number
        if profile.contact_phone:
            if profile.contact_phone.startswith("+"):
                orm_profile.phone_country_code = profile.contact_phone[:3]
                orm_profile.phone_number = profile.contact_phone[3:]
            else:
                orm_profile.phone_number = profile.contact_phone

        # Update JSON fields
        orm_profile.set_coaching_languages([lang.value for lang in profile.languages])
        orm_profile.set_certifications(profile.certifications)
        orm_profile.set_specialties(profile.specializations)

        # Convert communication tools to dict
        tools_dict = {tool.value: True for tool in profile.communication_tools}
        orm_profile.set_communication_tools(tools_dict)

    def _plan_legacy_to_domain(self, orm_plan: CoachingPlanModel) -> CoachingPlan:
        """Convert legacy CoachingPlan ORM model to domain model.

        Args:
            orm_plan: Legacy CoachingPlan ORM model

        Returns:
            CoachingPlan domain model
        """
        return CoachingPlan(
            id=UUID(str(orm_plan.id)) if orm_plan.id else None,
            coach_profile_id=(
                UUID(str(orm_plan.coach_profile_id))
                if orm_plan.coach_profile_id
                else None
            ),
            plan_type=orm_plan.plan_type or "single_session",
            title=orm_plan.title or "",
            description=orm_plan.description,
            duration_minutes=orm_plan.duration_minutes,
            number_of_sessions=orm_plan.number_of_sessions or 1,
            price=float(orm_plan.price) if orm_plan.price else 0.0,
            currency=orm_plan.currency or "NTD",
            is_active=(orm_plan.is_active if orm_plan.is_active is not None else True),
            max_participants=orm_plan.max_participants or 1,
            booking_notice_hours=orm_plan.booking_notice_hours or 24,
            cancellation_notice_hours=orm_plan.cancellation_notice_hours or 24,
            created_at=orm_plan.created_at,
            updated_at=orm_plan.updated_at,
        )

    def _plan_domain_to_legacy(self, plan: CoachingPlan) -> CoachingPlanModel:
        """Convert CoachingPlan domain model to legacy ORM model.

        Args:
            plan: CoachingPlan domain model

        Returns:
            Legacy CoachingPlan ORM model
        """
        return CoachingPlanModel(
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
        )

    def _update_plan_orm_from_domain(
        self, orm_plan: CoachingPlanModel, plan: CoachingPlan
    ):
        """Update existing CoachingPlan ORM model from domain model.

        Args:
            orm_plan: Existing legacy CoachingPlan ORM model
            plan: CoachingPlan domain model with updates
        """
        orm_plan.plan_type = plan.plan_type
        orm_plan.title = plan.title
        orm_plan.description = plan.description
        orm_plan.duration_minutes = plan.duration_minutes
        orm_plan.number_of_sessions = plan.number_of_sessions
        orm_plan.price = plan.price
        orm_plan.currency = plan.currency
        orm_plan.is_active = plan.is_active
        orm_plan.max_participants = plan.max_participants
        orm_plan.booking_notice_hours = plan.booking_notice_hours
        orm_plan.cancellation_notice_hours = plan.cancellation_notice_hours


def create_coach_profile_repository(
    session: DBSession,
) -> CoachProfileRepoPort:
    """Factory function to create a coach profile repository.

    Args:
        session: SQLAlchemy session

    Returns:
        CoachProfileRepoPort implementation
    """
    return SQLAlchemyCoachProfileRepository(session)
