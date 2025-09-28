"""Coach profile management use cases for Clean Architecture.

This module implements all business logic for coach profile operations,
including profile management and coaching plan management.
Following Clean Architecture principles with repository injection.
"""

from typing import List, Optional
from uuid import UUID

from ..models.coach_profile import CoachProfile
from ..models.coaching_plan import CoachingPlan
from ..repositories.ports import CoachProfileRepoPort, UserRepoPort


class CoachProfileManagementUseCase:
    """Use case for managing coach profiles and coaching plans."""

    def __init__(
        self,
        coach_profile_repo: CoachProfileRepoPort,
        user_repo: UserRepoPort,
    ):
        """Initialize use case with repository dependencies.

        Args:
            coach_profile_repo: Repository for coach profile operations
            user_repo: Repository for user operations
        """
        self.coach_profile_repo = coach_profile_repo
        self.user_repo = user_repo

    def get_profile(self, user_id: UUID) -> Optional[CoachProfile]:
        """Get coach profile for a user.

        Args:
            user_id: UUID of the user

        Returns:
            CoachProfile if found, None otherwise

        Raises:
            ValueError: If user doesn't exist
        """
        # Verify user exists
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        return self.coach_profile_repo.get_by_user_id(user_id)

    def create_profile(self, user_id: UUID, profile_data: CoachProfile) -> CoachProfile:
        """Create a new coach profile.

        Args:
            user_id: UUID of the user
            profile_data: CoachProfile domain entity with profile information

        Returns:
            Created CoachProfile domain entity

        Raises:
            ValueError: If user doesn't exist or profile already exists
        """
        # Verify user exists
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Check if profile already exists
        existing_profile = self.coach_profile_repo.get_by_user_id(user_id)
        if existing_profile:
            raise ValueError(f"Coach profile already exists for user {user_id}")

        # Set user_id on the profile
        profile_data.user_id = user_id

        return self.coach_profile_repo.save(profile_data)

    def update_profile(self, user_id: UUID, profile_data: CoachProfile) -> CoachProfile:
        """Update existing coach profile.

        Args:
            user_id: UUID of the user
            profile_data: CoachProfile domain entity with updated information

        Returns:
            Updated CoachProfile domain entity

        Raises:
            ValueError: If user doesn't exist or profile doesn't exist
        """
        # Verify user exists
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Check if profile exists
        existing_profile = self.coach_profile_repo.get_by_user_id(user_id)
        if not existing_profile:
            raise ValueError(f"Coach profile not found for user {user_id}")

        # Update profile with existing ID and user_id
        profile_data.id = existing_profile.id
        profile_data.user_id = user_id

        return self.coach_profile_repo.save(profile_data)

    def delete_profile(self, user_id: UUID) -> bool:
        """Delete coach profile.

        Args:
            user_id: UUID of the user

        Returns:
            True if profile was deleted, False if not found

        Raises:
            ValueError: If user doesn't exist
        """
        # Verify user exists
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        return self.coach_profile_repo.delete(user_id)

    def get_coaching_plans(self, user_id: UUID) -> List[CoachingPlan]:
        """Get all coaching plans for a user's profile.

        Args:
            user_id: UUID of the user

        Returns:
            List of CoachingPlan domain entities

        Raises:
            ValueError: If user doesn't exist or has no coach profile
        """
        # Verify user exists
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Get coach profile
        profile = self.coach_profile_repo.get_by_user_id(user_id)
        if not profile:
            raise ValueError(f"Coach profile not found for user {user_id}")

        return self.coach_profile_repo.get_coaching_plans_by_profile_id(profile.id)

    def create_plan(self, user_id: UUID, plan_data: CoachingPlan) -> CoachingPlan:
        """Create a new coaching plan.

        Args:
            user_id: UUID of the user
            plan_data: CoachingPlan domain entity with plan information

        Returns:
            Created CoachingPlan domain entity

        Raises:
            ValueError: If user doesn't exist or has no coach profile
        """
        # Verify user exists
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Get coach profile
        profile = self.coach_profile_repo.get_by_user_id(user_id)
        if not profile:
            raise ValueError(
                f"Coach profile not found for user {user_id}. Please create a coach profile first."
            )

        # Set coach_profile_id on the plan
        plan_data.coach_profile_id = profile.id

        return self.coach_profile_repo.save_coaching_plan(plan_data)

    def update_plan(
        self, user_id: UUID, plan_id: UUID, plan_data: CoachingPlan
    ) -> CoachingPlan:
        """Update existing coaching plan.

        Args:
            user_id: UUID of the user
            plan_id: UUID of the plan to update
            plan_data: CoachingPlan domain entity with updated information

        Returns:
            Updated CoachingPlan domain entity

        Raises:
            ValueError: If user doesn't exist, has no coach profile, or plan doesn't exist/belong to user
        """
        # Verify user exists
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Get coach profile
        profile = self.coach_profile_repo.get_by_user_id(user_id)
        if not profile:
            raise ValueError(f"Coach profile not found for user {user_id}")

        # Check if plan exists and belongs to this user's profile
        existing_plan = self.coach_profile_repo.get_coaching_plan_by_id(plan_id)
        if not existing_plan:
            raise ValueError(f"Coaching plan {plan_id} not found")

        if existing_plan.coach_profile_id != profile.id:
            raise ValueError(
                f"Coaching plan {plan_id} does not belong to user {user_id}"
            )

        # Update plan with existing ID and coach_profile_id
        plan_data.id = plan_id
        plan_data.coach_profile_id = profile.id

        return self.coach_profile_repo.save_coaching_plan(plan_data)

    def delete_plan(self, user_id: UUID, plan_id: UUID) -> bool:
        """Delete coaching plan.

        Args:
            user_id: UUID of the user
            plan_id: UUID of the plan to delete

        Returns:
            True if plan was deleted, False if not found

        Raises:
            ValueError: If user doesn't exist, has no coach profile, or plan doesn't belong to user
        """
        # Verify user exists
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Get coach profile
        profile = self.coach_profile_repo.get_by_user_id(user_id)
        if not profile:
            raise ValueError(f"Coach profile not found for user {user_id}")

        # Check if plan exists and belongs to this user's profile
        existing_plan = self.coach_profile_repo.get_coaching_plan_by_id(plan_id)
        if not existing_plan:
            return False  # Plan not found

        if existing_plan.coach_profile_id != profile.id:
            raise ValueError(
                f"Coaching plan {plan_id} does not belong to user {user_id}"
            )

        return self.coach_profile_repo.delete_coaching_plan(plan_id)

    def get_all_verified_coaches(self) -> List[CoachProfile]:
        """Get all verified coach profiles (public profiles).

        Returns:
            List of CoachProfile domain entities that are public
        """
        return self.coach_profile_repo.get_all_verified_coaches()
