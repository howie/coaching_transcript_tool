"""Test cases for coach profile API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from coaching_assistant.models import User, UserPlan, CoachProfile, CoachingPlan


class TestCoachProfileAPI:
    """Test cases for coach profile API endpoints."""

    @pytest.mark.asyncio
    async def test_get_coach_profile_not_exists(self, client: AsyncClient, auth_user: User):
        """Test getting coach profile when none exists."""
        response = await client.get("/api/coach-profile/")
        assert response.status_code == 200
        assert response.json() is None

    @pytest.mark.asyncio
    async def test_create_coach_profile(self, client: AsyncClient, auth_user: User):
        """Test creating a new coach profile."""
        profile_data = {
            "display_name": "Test Coach",
            "public_email": "test.coach@example.com",
            "phone_country_code": "+1",
            "phone_number": "555-0123",
            "country": "USA",
            "city": "San Francisco",
            "timezone": "America/Los_Angeles",
            "coaching_languages": ["english", "spanish"],
            "communication_tools": {
                "line": False,
                "zoom": True,
                "google_meet": True,
                "ms_teams": False
            },
            "line_id": "testcoach",
            "coach_experience": "advanced",
            "training_institution": "ICF",
            "certifications": ["ACC", "PCC"],
            "linkedin_url": "https://linkedin.com/in/testcoach",
            "personal_website": "https://testcoach.com",
            "bio": "Experienced executive coach with 10+ years in leadership development.",
            "specialties": ["Leadership", "Executive Coaching"],
            "is_public": True
        }
        
        response = await client.post("/api/coach-profile/", json=profile_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["display_name"] == "Test Coach"
        assert data["public_email"] == "test.coach@example.com"
        assert data["country"] == "USA"
        assert data["coaching_languages"] == ["english", "spanish"]
        assert data["communication_tools"]["zoom"] is True
        assert data["certifications"] == ["ACC", "PCC"]
        assert data["is_public"] is True
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_coach_profile_duplicate(self, client: AsyncClient, auth_user: User, db_session: AsyncSession):
        """Test creating coach profile when one already exists."""
        # Create existing profile
        existing_profile = CoachProfile(
            user_id=auth_user.id,
            display_name="Existing Coach",
            is_public=False
        )
        db_session.add(existing_profile)
        await db_session.commit()
        
        # Try to create another profile
        profile_data = {
            "display_name": "New Coach",
            "is_public": True
        }
        
        response = await client.post("/api/coach-profile/", json=profile_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_existing_coach_profile(self, client: AsyncClient, auth_user: User, db_session: AsyncSession):
        """Test getting an existing coach profile."""
        # Create profile
        profile = CoachProfile(
            user_id=auth_user.id,
            display_name="Existing Coach",
            public_email="existing@example.com",
            country="Canada",
            city="Toronto",
            coach_experience="intermediate",
            is_public=True
        )
        profile.set_coaching_languages(["english", "french"])
        profile.set_communication_tools({"zoom": True, "line": False})
        profile.set_certifications(["ACC"])
        profile.set_specialties(["Career Coaching"])
        
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)
        
        # Get profile
        response = await client.get("/api/coach-profile/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["display_name"] == "Existing Coach"
        assert data["public_email"] == "existing@example.com"
        assert data["country"] == "Canada"
        assert data["coaching_languages"] == ["english", "french"]
        assert data["communication_tools"]["zoom"] is True
        assert data["certifications"] == ["ACC"]
        assert data["specialties"] == ["Career Coaching"]
        assert data["is_public"] is True

    @pytest.mark.asyncio
    async def test_update_coach_profile(self, client: AsyncClient, auth_user: User, db_session: AsyncSession):
        """Test updating an existing coach profile."""
        # Create profile
        profile = CoachProfile(
            user_id=auth_user.id,
            display_name="Original Coach",
            country="USA",
            is_public=False
        )
        profile.set_coaching_languages(["english"])
        
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)
        
        # Update profile
        update_data = {
            "display_name": "Updated Coach",
            "country": "Canada",
            "coaching_languages": ["english", "french", "spanish"],
            "is_public": True
        }
        
        response = await client.put("/api/coach-profile/", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["display_name"] == "Updated Coach"
        assert data["country"] == "Canada"
        assert data["coaching_languages"] == ["english", "french", "spanish"]
        assert data["is_public"] is True

    @pytest.mark.asyncio
    async def test_update_nonexistent_coach_profile(self, client: AsyncClient, auth_user: User):
        """Test updating a coach profile that doesn't exist."""
        update_data = {
            "display_name": "Non-existent Coach"
        }
        
        response = await client.put("/api/coach-profile/", json=update_data)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_coach_profile(self, client: AsyncClient, auth_user: User, db_session: AsyncSession):
        """Test deleting a coach profile."""
        # Create profile
        profile = CoachProfile(
            user_id=auth_user.id,
            display_name="To Be Deleted",
            is_public=False
        )
        db_session.add(profile)
        await db_session.commit()
        
        # Delete profile
        response = await client.delete("/api/coach-profile/")
        assert response.status_code == 204
        
        # Verify profile is deleted
        response = await client.get("/api/coach-profile/")
        assert response.status_code == 200
        assert response.json() is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_coach_profile(self, client: AsyncClient, auth_user: User):
        """Test deleting a coach profile that doesn't exist."""
        response = await client.delete("/api/coach-profile/")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestCoachingPlanAPI:
    """Test cases for coaching plan API endpoints."""

    @pytest.mark.asyncio
    async def test_get_coaching_plans_no_profile(self, client: AsyncClient, auth_user: User):
        """Test getting coaching plans when no profile exists."""
        response = await client.get("/api/coach-profile/plans")
        assert response.status_code == 404
        assert "profile not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_empty_coaching_plans(self, client: AsyncClient, auth_user: User, db_session: AsyncSession):
        """Test getting coaching plans when profile exists but has no plans."""
        # Create profile
        profile = CoachProfile(
            user_id=auth_user.id,
            display_name="Plan Coach",
            is_public=True
        )
        db_session.add(profile)
        await db_session.commit()
        
        response = await client.get("/api/coach-profile/plans")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_create_coaching_plan(self, client: AsyncClient, auth_user: User, db_session: AsyncSession):
        """Test creating a new coaching plan."""
        # Create profile
        profile = CoachProfile(
            user_id=auth_user.id,
            display_name="Plan Coach",
            is_public=True
        )
        db_session.add(profile)
        await db_session.commit()
        
        # Create plan
        plan_data = {
            "plan_type": "single_session",
            "title": "Executive Coaching Session",
            "description": "One-on-one executive coaching",
            "duration_minutes": 90,
            "number_of_sessions": 1,
            "price": 250.0,
            "currency": "USD",
            "is_active": True,
            "max_participants": 1,
            "booking_notice_hours": 24,
            "cancellation_notice_hours": 24
        }
        
        response = await client.post("/api/coach-profile/plans", json=plan_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["title"] == "Executive Coaching Session"
        assert data["plan_type"] == "single_session"
        assert data["duration_minutes"] == 90
        assert data["price"] == 250.0
        assert data["currency"] == "USD"
        assert data["is_active"] is True
        assert data["price_per_session"] == 250.0
        assert data["total_duration_minutes"] == 90
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_coaching_plan_no_profile(self, client: AsyncClient, auth_user: User):
        """Test creating a coaching plan when no profile exists."""
        plan_data = {
            "plan_type": "single_session",
            "title": "Test Session",
            "price": 100.0
        }
        
        response = await client.post("/api/coach-profile/plans", json=plan_data)
        assert response.status_code == 404
        assert "profile not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_coaching_plans_with_plans(self, client: AsyncClient, auth_user: User, db_session: AsyncSession):
        """Test getting coaching plans when they exist."""
        # Create profile
        profile = CoachProfile(
            user_id=auth_user.id,
            display_name="Multi Plan Coach",
            is_public=True
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)
        
        # Create multiple plans
        plan1 = CoachingPlan(
            coach_profile_id=profile.id,
            plan_type="single_session",
            title="Single Session",
            duration_minutes=60,
            price=150.0
        )
        plan2 = CoachingPlan(
            coach_profile_id=profile.id,
            plan_type="package",
            title="4-Session Package",
            duration_minutes=90,
            number_of_sessions=4,
            price=500.0,
            is_active=True
        )
        
        db_session.add_all([plan1, plan2])
        await db_session.commit()
        
        # Get plans
        response = await client.get("/api/coach-profile/plans")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        
        titles = [plan["title"] for plan in data]
        assert "Single Session" in titles
        assert "4-Session Package" in titles
        
        # Find the package plan and check computed properties
        package_plan = next(p for p in data if p["title"] == "4-Session Package")
        assert package_plan["price_per_session"] == 125.0  # 500 / 4
        assert package_plan["total_duration_minutes"] == 360  # 90 * 4

    @pytest.mark.asyncio
    async def test_update_coaching_plan(self, client: AsyncClient, auth_user: User, db_session: AsyncSession):
        """Test updating a coaching plan."""
        # Create profile and plan
        profile = CoachProfile(
            user_id=auth_user.id,
            display_name="Update Coach",
            is_public=True
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)
        
        plan = CoachingPlan(
            coach_profile_id=profile.id,
            plan_type="single_session",
            title="Original Plan",
            price=100.0,
            duration_minutes=60
        )
        db_session.add(plan)
        await db_session.commit()
        await db_session.refresh(plan)
        
        # Update plan
        update_data = {
            "title": "Updated Plan",
            "price": 200.0,
            "duration_minutes": 90,
            "is_active": False
        }
        
        response = await client.put(f"/api/coach-profile/plans/{plan.id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == "Updated Plan"
        assert data["price"] == 200.0
        assert data["duration_minutes"] == 90
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_update_nonexistent_coaching_plan(self, client: AsyncClient, auth_user: User, db_session: AsyncSession):
        """Test updating a coaching plan that doesn't exist."""
        # Create profile
        profile = CoachProfile(
            user_id=auth_user.id,
            display_name="Test Coach",
            is_public=True
        )
        db_session.add(profile)
        await db_session.commit()
        
        # Try to update non-existent plan
        import uuid
        fake_id = uuid.uuid4()
        update_data = {"title": "Updated Plan"}
        
        response = await client.put(f"/api/coach-profile/plans/{fake_id}", json=update_data)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_coaching_plan(self, client: AsyncClient, auth_user: User, db_session: AsyncSession):
        """Test deleting a coaching plan."""
        # Create profile and plan
        profile = CoachProfile(
            user_id=auth_user.id,
            display_name="Delete Coach",
            is_public=True
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)
        
        plan = CoachingPlan(
            coach_profile_id=profile.id,
            plan_type="single_session",
            title="To Be Deleted",
            price=100.0
        )
        db_session.add(plan)
        await db_session.commit()
        await db_session.refresh(plan)
        
        # Delete plan
        response = await client.delete(f"/api/coach-profile/plans/{plan.id}")
        assert response.status_code == 204
        
        # Verify plan is deleted
        response = await client.get("/api/coach-profile/plans")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_delete_nonexistent_coaching_plan(self, client: AsyncClient, auth_user: User, db_session: AsyncSession):
        """Test deleting a coaching plan that doesn't exist."""
        # Create profile
        profile = CoachProfile(
            user_id=auth_user.id,
            display_name="Test Coach",
            is_public=True
        )
        db_session.add(profile)
        await db_session.commit()
        
        # Try to delete non-existent plan
        import uuid
        fake_id = uuid.uuid4()
        
        response = await client.delete(f"/api/coach-profile/plans/{fake_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_coaching_plan_validation(self, client: AsyncClient, auth_user: User, db_session: AsyncSession):
        """Test coaching plan validation."""
        # Create profile
        profile = CoachProfile(
            user_id=auth_user.id,
            display_name="Validation Coach",
            is_public=True
        )
        db_session.add(profile)
        await db_session.commit()
        
        # Test invalid plan data
        invalid_plan = {
            "plan_type": "",  # Empty type
            "title": "",  # Empty title
            "price": -100,  # Negative price
            "duration_minutes": 0  # Zero duration
        }
        
        response = await client.post("/api/coach-profile/plans", json=invalid_plan)
        assert response.status_code == 422  # Validation error