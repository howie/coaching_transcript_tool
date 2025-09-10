"""Test cases for coach profile models."""

import pytest
from sqlalchemy.orm import Session

from coaching_assistant.models import (
    CoachProfile,
    CoachingPlan,
    User,
    UserPlan,
)


class TestCoachProfile:
    """Test cases for CoachProfile model."""

    def test_create_coach_profile(self, db_session: Session):
        """Test creating a coach profile."""
        # Create a user first
        user = User(
            email="coach@example.com", name="Test Coach", plan=UserPlan.FREE
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Create coach profile
        profile = CoachProfile(
            user_id=user.id,
            display_name="Coach Smith",
            public_email="coach.smith@example.com",
            phone_country_code="+1",
            phone_number="555-0123",
            country="USA",
            city="New York",
            timezone="America/New_York",
            line_id="coachsmith",
            coach_experience="advanced",
            training_institution="ICF",
            linkedin_url="https://linkedin.com/in/coachsmith",
            personal_website="https://coachsmith.com",
            bio="Experienced executive coach specializing in leadership development.",
            is_public=True,
        )

        # Set JSON fields
        profile.set_coaching_languages(["english", "spanish"])
        profile.set_communication_tools({"zoom": True, "google_meet": True})
        profile.set_certifications(["PCC", "ACC"])
        profile.set_specialties(["Leadership", "Executive Coaching"])

        db_session.add(profile)
        db_session.commit()
        db_session.refresh(profile)

        # Verify the profile was created correctly
        assert profile.id is not None
        assert profile.user_id == user.id
        assert profile.display_name == "Coach Smith"
        assert profile.is_public is True

        # Test JSON fields
        assert profile.get_coaching_languages() == ["english", "spanish"]
        assert profile.get_communication_tools() == {
            "zoom": True,
            "google_meet": True,
        }
        assert profile.get_certifications() == ["PCC", "ACC"]
        assert profile.get_specialties() == [
            "Leadership",
            "Executive Coaching",
        ]

    def test_coach_profile_relationship_with_user(self, db_session: Session):
        """Test the relationship between CoachProfile and User."""
        # Create user
        user = User(
            email="relationship@example.com",
            name="Relationship Test",
            plan=UserPlan.PRO,
        )
        db_session.add(user)
        db_session.commit()

        # Create coach profile
        profile = CoachProfile(
            user_id=user.id, display_name="Relationship Coach", is_public=False
        )
        db_session.add(profile)
        db_session.commit()
        db_session.refresh(profile)
        db_session.refresh(user)

        # Test forward relationship
        assert profile.user == user

        # Test reverse relationship
        assert user.coach_profile == profile
        assert user.coach_profile.display_name == "Relationship Coach"

    def test_coach_profile_json_field_handling(self, db_session: Session):
        """Test JSON field getter/setter methods."""
        user = User(
            email="json@example.com", name="JSON Test", plan=UserPlan.FREE
        )
        db_session.add(user)
        db_session.commit()

        profile = CoachProfile(user_id=user.id, display_name="JSON Coach")
        db_session.add(profile)
        db_session.commit()

        # Test empty defaults
        assert profile.get_coaching_languages() == []
        assert profile.get_communication_tools() == {}
        assert profile.get_certifications() == []
        assert profile.get_specialties() == []

        # Test setting and getting values
        languages = ["mandarin", "english", "japanese"]
        profile.set_coaching_languages(languages)
        assert profile.get_coaching_languages() == languages

        tools = {"line": True, "zoom": False, "google_meet": True}
        profile.set_communication_tools(tools)
        assert profile.get_communication_tools() == tools

        certs = ["ICF-PCC", "Gallup-Certified"]
        profile.set_certifications(certs)
        assert profile.get_certifications() == certs

        specialties = ["Career Coaching", "Life Coaching"]
        profile.set_specialties(specialties)
        assert profile.get_specialties() == specialties

        db_session.commit()

    def test_coach_profile_invalid_json_handling(self, db_session: Session):
        """Test handling of invalid JSON data in database."""
        user = User(
            email="invalid@example.com",
            name="Invalid Test",
            plan=UserPlan.FREE,
        )
        db_session.add(user)
        db_session.commit()

        profile = CoachProfile(
            user_id=user.id,
            display_name="Invalid Coach",
            # Set invalid JSON manually
            coaching_languages="invalid json",
            communication_tools="also invalid",
            certifications="not json either",
            specialties="definitely not json",
        )
        db_session.add(profile)
        db_session.commit()

        # Should return empty defaults for invalid JSON
        assert profile.get_coaching_languages() == []
        assert profile.get_communication_tools() == {}
        assert profile.get_certifications() == []
        assert profile.get_specialties() == []


class TestCoachingPlan:
    """Test cases for CoachingPlan model."""

    def test_create_coaching_plan(self, db_session: Session):
        """Test creating a coaching plan."""
        # Create user and coach profile
        user = User(
            email="plan@example.com", name="Plan Test", plan=UserPlan.PRO
        )
        db_session.add(user)
        db_session.commit()

        profile = CoachProfile(user_id=user.id, display_name="Plan Coach")
        db_session.add(profile)
        db_session.commit()

        # Create coaching plan
        plan = CoachingPlan(
            coach_profile_id=profile.id,
            plan_type="single_session",
            title="Executive Coaching Session",
            description="One-on-one executive coaching session",
            duration_minutes=90,
            number_of_sessions=1,
            price=250.0,
            currency="USD",
            max_participants=1,
            booking_notice_hours=24,
            cancellation_notice_hours=12,
            is_active=True,
        )
        db_session.add(plan)
        db_session.commit()
        db_session.refresh(plan)

        # Verify plan creation
        assert plan.id is not None
        assert plan.coach_profile_id == profile.id
        assert plan.title == "Executive Coaching Session"
        assert plan.price == 250.0
        assert plan.is_active is True

    def test_coaching_plan_relationship_with_profile(
        self, db_session: Session
    ):
        """Test the relationship between CoachingPlan and CoachProfile."""
        # Create user and coach profile
        user = User(
            email="plan_relationship@example.com",
            name="Plan Relationship Test",
            plan=UserPlan.PRO,
        )
        db_session.add(user)
        db_session.commit()

        profile = CoachProfile(
            user_id=user.id, display_name="Relationship Plan Coach"
        )
        db_session.add(profile)
        db_session.commit()

        # Create multiple plans
        plan1 = CoachingPlan(
            coach_profile_id=profile.id,
            plan_type="single_session",
            title="Plan 1",
            price=100.0,
        )
        plan2 = CoachingPlan(
            coach_profile_id=profile.id,
            plan_type="package",
            title="Plan 2",
            price=400.0,
            number_of_sessions=4,
        )

        db_session.add_all([plan1, plan2])
        db_session.commit()
        db_session.refresh(profile)

        # Test relationships
        assert plan1.coach_profile == profile
        assert plan2.coach_profile == profile

        # Test reverse relationship
        plans = list(profile.coaching_plans)
        assert len(plans) == 2
        plan_titles = [p.title for p in plans]
        assert "Plan 1" in plan_titles
        assert "Plan 2" in plan_titles

    def test_coaching_plan_computed_properties(self):
        """Test computed properties of CoachingPlan."""
        # Single session plan
        single_plan = CoachingPlan(
            plan_type="single_session",
            title="Single Session",
            duration_minutes=90,
            number_of_sessions=1,
            price=200.0,
        )

        assert single_plan.price_per_session == 200.0
        assert single_plan.total_duration_minutes == 90

        # Package plan
        package_plan = CoachingPlan(
            plan_type="package",
            title="4-Session Package",
            duration_minutes=60,
            number_of_sessions=4,
            price=600.0,
        )

        assert package_plan.price_per_session == 150.0  # 600 / 4
        assert package_plan.total_duration_minutes == 240  # 60 * 4

        # Plan with no sessions (edge case)
        no_sessions_plan = CoachingPlan(
            plan_type="custom",
            title="Custom Plan",
            duration_minutes=120,
            number_of_sessions=0,
            price=300.0,
        )

        assert (
            no_sessions_plan.price_per_session == 300.0
        )  # fallback to total price
        assert no_sessions_plan.total_duration_minutes == 0

    def test_cascade_delete_coach_profile(self, db_session: Session):
        """Test that deleting a coach profile cascades to coaching plans."""
        # Create user and coach profile
        user = User(
            email="cascade@example.com", name="Cascade Test", plan=UserPlan.PRO
        )
        db_session.add(user)
        db_session.commit()

        profile = CoachProfile(user_id=user.id, display_name="Cascade Coach")
        db_session.add(profile)
        db_session.commit()

        # Create coaching plans
        plan1 = CoachingPlan(
            coach_profile_id=profile.id,
            plan_type="single_session",
            title="Plan 1",
            price=100.0,
        )
        plan2 = CoachingPlan(
            coach_profile_id=profile.id,
            plan_type="package",
            title="Plan 2",
            price=400.0,
        )

        db_session.add_all([plan1, plan2])
        db_session.commit()

        plan1_id = plan1.id
        plan2_id = plan2.id
        profile_id = profile.id

        # Delete coach profile
        db_session.delete(profile)
        db_session.commit()

        # Verify cascade delete
        assert db_session.get(CoachProfile, profile_id) is None
        assert db_session.get(CoachingPlan, plan1_id) is None
        assert db_session.get(CoachingPlan, plan2_id) is None

    def test_unique_user_coach_profile(self, db_session: Session):
        """Test that a user can only have one coach profile."""
        user = User(
            email="unique@example.com", name="Unique Test", plan=UserPlan.PRO
        )
        db_session.add(user)
        db_session.commit()

        # Create first profile
        profile1 = CoachProfile(user_id=user.id, display_name="First Profile")
        db_session.add(profile1)
        db_session.commit()

        # Try to create second profile for same user - should fail
        profile2 = CoachProfile(user_id=user.id, display_name="Second Profile")
        db_session.add(profile2)

        with pytest.raises(Exception):  # Should raise constraint violation
            db_session.commit()
