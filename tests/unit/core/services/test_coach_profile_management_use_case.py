"""Unit tests for CoachProfileManagementUseCase."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.coaching_assistant.core.models.coach_profile import (
    CoachExperience,
    CoachingLanguage,
    CoachProfile,
    CommunicationTool,
)
from src.coaching_assistant.core.models.coaching_plan import CoachingPlan
from src.coaching_assistant.core.models.user import User, UserPlan
from src.coaching_assistant.core.services.coach_profile_management_use_case import (
    CoachProfileManagementUseCase,
)


class TestCoachProfileManagementUseCase:
    """Test cases for CoachProfileManagementUseCase."""

    def setup_method(self):
        """Set up test dependencies."""
        self.mock_coach_profile_repo = Mock()
        self.mock_user_repo = Mock()

        self.use_case = CoachProfileManagementUseCase(
            coach_profile_repo=self.mock_coach_profile_repo,
            user_repo=self.mock_user_repo,
        )

        # Sample data
        self.user_id = uuid4()
        self.profile_id = uuid4()
        self.plan_id = uuid4()

        self.sample_user = User(
            id=self.user_id,
            email="coach@example.com",
            plan=UserPlan.PRO,
        )

        self.sample_profile = CoachProfile(
            id=self.profile_id,
            user_id=self.user_id,
            public_name="John Doe",
            bio="Experienced coach",
            experience_level=CoachExperience.ADVANCED,
            languages=[CoachingLanguage.ENGLISH, CoachingLanguage.MANDARIN],
            communication_tools=[
                CommunicationTool.ZOOM,
                CommunicationTool.LINE,
            ],
            is_public=True,
        )

        self.sample_plan = CoachingPlan(
            id=self.plan_id,
            coach_profile_id=self.profile_id,
            title="Individual Coaching",
            plan_type="single_session",
            price=100.0,
            currency="USD",
            duration_minutes=60,
        )

    def test_get_profile_success(self):
        """Test successful profile retrieval."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = self.sample_user
        self.mock_coach_profile_repo.get_by_user_id.return_value = self.sample_profile

        # Act
        result = self.use_case.get_profile(self.user_id)

        # Assert
        assert result == self.sample_profile
        self.mock_user_repo.get_by_id.assert_called_once_with(self.user_id)
        self.mock_coach_profile_repo.get_by_user_id.assert_called_once_with(
            self.user_id
        )

    def test_get_profile_user_not_found(self):
        """Test profile retrieval when user doesn't exist."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="User .* not found"):
            self.use_case.get_profile(self.user_id)

    def test_get_profile_not_found(self):
        """Test profile retrieval when profile doesn't exist."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = self.sample_user
        self.mock_coach_profile_repo.get_by_user_id.return_value = None

        # Act
        result = self.use_case.get_profile(self.user_id)

        # Assert
        assert result is None

    def test_create_profile_success(self):
        """Test successful profile creation."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = self.sample_user
        self.mock_coach_profile_repo.get_by_user_id.return_value = None
        self.mock_coach_profile_repo.save.return_value = self.sample_profile

        profile_data = CoachProfile(
            public_name="John Doe",
            bio="Experienced coach",
        )

        # Act
        result = self.use_case.create_profile(self.user_id, profile_data)

        # Assert
        assert result == self.sample_profile
        assert profile_data.user_id == self.user_id
        self.mock_coach_profile_repo.save.assert_called_once_with(profile_data)

    def test_create_profile_user_not_found(self):
        """Test profile creation when user doesn't exist."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = None

        profile_data = CoachProfile(public_name="John Doe")

        # Act & Assert
        with pytest.raises(ValueError, match="User .* not found"):
            self.use_case.create_profile(self.user_id, profile_data)

    def test_create_profile_already_exists(self):
        """Test profile creation when profile already exists."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = self.sample_user
        self.mock_coach_profile_repo.get_by_user_id.return_value = self.sample_profile

        profile_data = CoachProfile(public_name="John Doe")

        # Act & Assert
        with pytest.raises(ValueError, match="Coach profile already exists"):
            self.use_case.create_profile(self.user_id, profile_data)

    def test_update_profile_success(self):
        """Test successful profile update."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = self.sample_user
        self.mock_coach_profile_repo.get_by_user_id.return_value = self.sample_profile

        updated_profile = CoachProfile(
            public_name="Jane Doe",
            bio="Updated bio",
        )
        self.mock_coach_profile_repo.save.return_value = updated_profile

        # Act
        result = self.use_case.update_profile(self.user_id, updated_profile)

        # Assert
        assert result == updated_profile
        assert updated_profile.id == self.profile_id
        assert updated_profile.user_id == self.user_id
        self.mock_coach_profile_repo.save.assert_called_once_with(updated_profile)

    def test_update_profile_not_found(self):
        """Test profile update when profile doesn't exist."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = self.sample_user
        self.mock_coach_profile_repo.get_by_user_id.return_value = None

        profile_data = CoachProfile(public_name="Jane Doe")

        # Act & Assert
        with pytest.raises(ValueError, match="Coach profile not found"):
            self.use_case.update_profile(self.user_id, profile_data)

    def test_delete_profile_success(self):
        """Test successful profile deletion."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = self.sample_user
        self.mock_coach_profile_repo.delete.return_value = True

        # Act
        result = self.use_case.delete_profile(self.user_id)

        # Assert
        assert result is True
        self.mock_coach_profile_repo.delete.assert_called_once_with(self.user_id)

    def test_delete_profile_not_found(self):
        """Test profile deletion when profile doesn't exist."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = self.sample_user
        self.mock_coach_profile_repo.delete.return_value = False

        # Act
        result = self.use_case.delete_profile(self.user_id)

        # Assert
        assert result is False

    def test_get_coaching_plans_success(self):
        """Test successful coaching plans retrieval."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = self.sample_user
        self.mock_coach_profile_repo.get_by_user_id.return_value = self.sample_profile
        self.mock_coach_profile_repo.get_coaching_plans_by_profile_id.return_value = [
            self.sample_plan
        ]

        # Act
        result = self.use_case.get_coaching_plans(self.user_id)

        # Assert
        assert result == [self.sample_plan]
        self.mock_coach_profile_repo.get_coaching_plans_by_profile_id.assert_called_once_with(
            self.profile_id
        )

    def test_get_coaching_plans_no_profile(self):
        """Test coaching plans retrieval when profile doesn't exist."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = self.sample_user
        self.mock_coach_profile_repo.get_by_user_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Coach profile not found"):
            self.use_case.get_coaching_plans(self.user_id)

    def test_create_plan_success(self):
        """Test successful coaching plan creation."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = self.sample_user
        self.mock_coach_profile_repo.get_by_user_id.return_value = self.sample_profile
        self.mock_coach_profile_repo.save_coaching_plan.return_value = self.sample_plan

        plan_data = CoachingPlan(
            title="Individual Coaching",
            plan_type="single_session",
            price=100.0,
        )

        # Act
        result = self.use_case.create_plan(self.user_id, plan_data)

        # Assert
        assert result == self.sample_plan
        assert plan_data.coach_profile_id == self.profile_id
        self.mock_coach_profile_repo.save_coaching_plan.assert_called_once_with(
            plan_data
        )

    def test_create_plan_no_profile(self):
        """Test coaching plan creation when profile doesn't exist."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = self.sample_user
        self.mock_coach_profile_repo.get_by_user_id.return_value = None

        plan_data = CoachingPlan(title="Individual Coaching")

        # Act & Assert
        with pytest.raises(ValueError, match="Coach profile not found"):
            self.use_case.create_plan(self.user_id, plan_data)

    def test_update_plan_success(self):
        """Test successful coaching plan update."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = self.sample_user
        self.mock_coach_profile_repo.get_by_user_id.return_value = self.sample_profile
        self.mock_coach_profile_repo.get_coaching_plan_by_id.return_value = (
            self.sample_plan
        )

        updated_plan = CoachingPlan(
            title="Updated Coaching",
            price=150.0,
        )
        self.mock_coach_profile_repo.save_coaching_plan.return_value = updated_plan

        # Act
        result = self.use_case.update_plan(self.user_id, self.plan_id, updated_plan)

        # Assert
        assert result == updated_plan
        assert updated_plan.id == self.plan_id
        assert updated_plan.coach_profile_id == self.profile_id
        self.mock_coach_profile_repo.save_coaching_plan.assert_called_once_with(
            updated_plan
        )

    def test_update_plan_not_found(self):
        """Test coaching plan update when plan doesn't exist."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = self.sample_user
        self.mock_coach_profile_repo.get_by_user_id.return_value = self.sample_profile
        self.mock_coach_profile_repo.get_coaching_plan_by_id.return_value = None

        plan_data = CoachingPlan(title="Updated Coaching")

        # Act & Assert
        with pytest.raises(ValueError, match="Coaching plan .* not found"):
            self.use_case.update_plan(self.user_id, self.plan_id, plan_data)

    def test_update_plan_wrong_owner(self):
        """Test coaching plan update when plan belongs to different user."""
        # Arrange
        other_profile_id = uuid4()
        wrong_plan = CoachingPlan(
            id=self.plan_id,
            coach_profile_id=other_profile_id,
            title="Wrong Owner Plan",
        )

        self.mock_user_repo.get_by_id.return_value = self.sample_user
        self.mock_coach_profile_repo.get_by_user_id.return_value = self.sample_profile
        self.mock_coach_profile_repo.get_coaching_plan_by_id.return_value = wrong_plan

        plan_data = CoachingPlan(title="Updated Coaching")

        # Act & Assert
        with pytest.raises(ValueError, match="does not belong to user"):
            self.use_case.update_plan(self.user_id, self.plan_id, plan_data)

    def test_delete_plan_success(self):
        """Test successful coaching plan deletion."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = self.sample_user
        self.mock_coach_profile_repo.get_by_user_id.return_value = self.sample_profile
        self.mock_coach_profile_repo.get_coaching_plan_by_id.return_value = (
            self.sample_plan
        )
        self.mock_coach_profile_repo.delete_coaching_plan.return_value = True

        # Act
        result = self.use_case.delete_plan(self.user_id, self.plan_id)

        # Assert
        assert result is True
        self.mock_coach_profile_repo.delete_coaching_plan.assert_called_once_with(
            self.plan_id
        )

    def test_delete_plan_not_found(self):
        """Test coaching plan deletion when plan doesn't exist."""
        # Arrange
        self.mock_user_repo.get_by_id.return_value = self.sample_user
        self.mock_coach_profile_repo.get_by_user_id.return_value = self.sample_profile
        self.mock_coach_profile_repo.get_coaching_plan_by_id.return_value = None

        # Act
        result = self.use_case.delete_plan(self.user_id, self.plan_id)

        # Assert
        assert result is False
        self.mock_coach_profile_repo.delete_coaching_plan.assert_not_called()

    def test_delete_plan_wrong_owner(self):
        """Test coaching plan deletion when plan belongs to different user."""
        # Arrange
        other_profile_id = uuid4()
        wrong_plan = CoachingPlan(
            id=self.plan_id,
            coach_profile_id=other_profile_id,
            title="Wrong Owner Plan",
        )

        self.mock_user_repo.get_by_id.return_value = self.sample_user
        self.mock_coach_profile_repo.get_by_user_id.return_value = self.sample_profile
        self.mock_coach_profile_repo.get_coaching_plan_by_id.return_value = wrong_plan

        # Act & Assert
        with pytest.raises(ValueError, match="does not belong to user"):
            self.use_case.delete_plan(self.user_id, self.plan_id)

    def test_get_all_verified_coaches(self):
        """Test getting all verified coaches."""
        # Arrange
        verified_coaches = [self.sample_profile]
        self.mock_coach_profile_repo.get_all_verified_coaches.return_value = (
            verified_coaches
        )

        # Act
        result = self.use_case.get_all_verified_coaches()

        # Assert
        assert result == verified_coaches
        self.mock_coach_profile_repo.get_all_verified_coaches.assert_called_once()
