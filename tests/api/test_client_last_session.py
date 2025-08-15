"""Test getting client's last session endpoint."""

import pytest
from datetime import date
from uuid import uuid4
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from coaching_assistant.models import User, Client, CoachingSession
from coaching_assistant.models.user import UserPlan


class TestClientLastSession:
    """Test the get client last session endpoint."""

    def test_get_client_last_session_no_sessions(self, db_session: Session, api_client: TestClient, sample_user: User, sample_token: str):
        """Test getting last session when client has no sessions."""
        # Create a client
        client = Client(
            user_id=sample_user.id,
            name="Test Client",
            email="client@test.com"
        )
        db_session.add(client)
        db_session.commit()
        
        # Get last session - should return None
        response = api_client.get(
            f"/api/v1/coaching-sessions/clients/{client.id}/last-session",
            headers={"Authorization": f"Bearer {sample_token}"}
        )
        assert response.status_code == 200
        assert response.json() is None

    def test_get_client_last_session_with_sessions(self, db_session: Session, api_client: TestClient, sample_user: User, sample_token: str):
        """Test getting last session when client has multiple sessions."""
        # Create a client
        client = Client(
            user_id=sample_user.id,
            name="Test Client",
            email="client@test.com"
        )
        db_session.add(client)
        db_session.commit()
        
        # Create first session (older)
        session1 = CoachingSession(
            coach_id=sample_user.id,
            client_id=client.id,
            session_date=date(2024, 1, 1),
            duration_min=60,
            fee_currency="TWD",
            fee_amount=2000
        )
        db_session.add(session1)
        
        # Create second session (newer)
        session2 = CoachingSession(
            coach_id=sample_user.id,
            client_id=client.id,
            session_date=date(2024, 1, 15),
            duration_min=90,
            fee_currency="USD",
            fee_amount=100
        )
        db_session.add(session2)
        
        # Create third session (newest)
        session3 = CoachingSession(
            coach_id=sample_user.id,
            client_id=client.id,
            session_date=date(2024, 2, 1),
            duration_min=120,
            fee_currency="EUR",
            fee_amount=150
        )
        db_session.add(session3)
        db_session.commit()
        
        # Get last session - should return session3 values (newest date)
        response = api_client.get(
            f"/api/v1/coaching-sessions/clients/{client.id}/last-session",
            headers={"Authorization": f"Bearer {sample_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data is not None
        assert data["duration_min"] == 120
        assert data["fee_currency"] == "EUR"
        assert data["fee_amount"] == 150

    def test_get_client_last_session_different_coach(self, db_session: Session, api_client: TestClient, sample_user: User, sample_token: str):
        """Test that coaches can only see their own sessions."""
        # Create another user (different coach)
        other_coach = User(
            email="other@example.com",
            name="Other Coach",
            google_id="987654321",
            plan=UserPlan.FREE
        )
        db_session.add(other_coach)
        
        # Create a client for the other coach
        client = Client(
            user_id=other_coach.id,
            name="Other Coach's Client",
            email="other.client@test.com"
        )
        db_session.add(client)
        db_session.commit()
        
        # Create session for other coach
        session = CoachingSession(
            coach_id=other_coach.id,
            client_id=client.id,
            session_date=date(2024, 1, 1),
            duration_min=60,
            fee_currency="TWD",
            fee_amount=2000
        )
        db_session.add(session)
        db_session.commit()
        
        # Try to get last session as sample_user - should return None (no access)
        response = api_client.get(
            f"/api/v1/coaching-sessions/clients/{client.id}/last-session",
            headers={"Authorization": f"Bearer {sample_token}"}
        )
        assert response.status_code == 200
        assert response.json() is None

    def test_get_client_last_session_invalid_client(self, api_client: TestClient, sample_token: str):
        """Test getting last session for non-existent client."""
        invalid_client_id = uuid4()
        
        response = api_client.get(
            f"/api/v1/coaching-sessions/clients/{invalid_client_id}/last-session",
            headers={"Authorization": f"Bearer {sample_token}"}
        )
        assert response.status_code == 200
        assert response.json() is None