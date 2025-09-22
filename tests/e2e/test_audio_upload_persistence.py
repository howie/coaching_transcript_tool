"""E2E test for audio upload transcription_session_id persistence bug.

This test reproduces and verifies the fix for the bug where:
1. User uploads audio file
2. Frontend updates coaching session with transcription_session_id
3. User navigates away and returns
4. transcription_session_id should still be persisted (was becoming null)
"""

import pytest
import json
from datetime import date
from uuid import uuid4


@pytest.fixture
def coaching_session_id(authenticated_client, test_user):
    """Create a coaching session for testing."""
    # First create a client
    client_response = authenticated_client.post(
        "/api/v1/clients",
        json={
            "name": "E2E Test Client",
            "email": "e2e@example.com",
            "notes": "Test client for E2E testing"
        }
    )
    assert client_response.status_code in [200, 201]  # 200 if client exists, 201 if created
    client_data = client_response.json()
    client_id = client_data["id"]

    # Create coaching session
    session_response = authenticated_client.post(
        "/api/v1/coaching-sessions",
        json={
            "session_date": str(date.today()),
            "client_id": client_id,
            "source": "CLIENT",
            "duration_min": 60,
            "fee_currency": "TWD",
            "fee_amount": 2000,
            "notes": "E2E test session"
        }
    )
    assert session_response.status_code == 201
    session_data = session_response.json()

    return session_data["id"]


def test_audio_upload_transcription_session_id_persistence(authenticated_client, coaching_session_id):
    """Test the complete audio upload flow and verify transcription_session_id persists.

    This reproduces the exact bug reported:
    1. Create coaching session (transcription_session_id = null)
    2. Create transcription session (simulates audio upload)
    3. Update coaching session with transcription_session_id
    4. Navigate away (new request) and verify persistence
    """

    # Step 1: Verify initial state - transcription_session_id should be null
    initial_response = authenticated_client.get(f"/api/v1/coaching-sessions/{coaching_session_id}")
    assert initial_response.status_code == 200
    initial_data = initial_response.json()
    assert initial_data["transcription_session_id"] is None

    # Step 2: Create a transcription session (simulates audio upload)
    transcription_response = authenticated_client.post(
        "/sessions",
        json={
            "title": "E2E Test Audio Upload",
            "language": "cmn-Hant-TW",
            "stt_provider": "google"
        }
    )
    assert transcription_response.status_code == 201
    transcription_data = transcription_response.json()
    transcription_session_id = transcription_data["id"]

    # Step 3: Update coaching session with transcription_session_id
    # This simulates the AudioUploader calling the update API
    update_response = authenticated_client.patch(
        f"/api/v1/coaching-sessions/{coaching_session_id}",
        json={
            "transcription_session_id": transcription_session_id
        }
    )
    assert update_response.status_code == 200
    update_data = update_response.json()
    assert update_data["transcription_session_id"] == transcription_session_id

    # Step 4: CRITICAL TEST - Simulate navigation away and return
    # This is where the bug was detected - data should persist across requests
    persistence_response = authenticated_client.get(f"/api/v1/coaching-sessions/{coaching_session_id}")
    assert persistence_response.status_code == 200
    persistence_data = persistence_response.json()

    # The critical assertion - this was failing before the database fix
    assert persistence_data["transcription_session_id"] == transcription_session_id
    assert persistence_data["transcription_session_id"] is not None

    # Additional verification - check that we can retrieve the transcription session
    transcription_check = authenticated_client.get(f"/sessions/{transcription_session_id}")
    assert transcription_check.status_code == 200
    transcription_check_data = transcription_check.json()
    assert transcription_check_data["title"] == "E2E Test Audio Upload"


def test_multiple_session_updates_persist(authenticated_client, coaching_session_id):
    """Test that multiple updates to the same session persist correctly."""

    # Create multiple transcription sessions
    transcription_ids = []
    for i in range(3):
        response = authenticated_client.post(
            "/sessions",
            json={
                "title": f"Multiple Update Test {i+1}",
                "language": "en-US",
                "stt_provider": "google"
            }
        )
        assert response.status_code == 201
        transcription_ids.append(response.json()["id"])

    # Update the coaching session multiple times
    for i, transcription_id in enumerate(transcription_ids):
        update_response = authenticated_client.patch(
            f"/api/v1/coaching-sessions/{coaching_session_id}",
            json={
                "transcription_session_id": transcription_id,
                "notes": f"Updated with transcription {i+1}"
            }
        )
        assert update_response.status_code == 200

        # Verify immediate persistence
        check_response = authenticated_client.get(f"/api/v1/coaching-sessions/{coaching_session_id}")
        assert check_response.status_code == 200
        check_data = check_response.json()
        assert check_data["transcription_session_id"] == transcription_id
        assert check_data["notes"] == f"Updated with transcription {i+1}"

    # Final verification - last update should be persisted
    final_response = authenticated_client.get(f"/api/v1/coaching-sessions/{coaching_session_id}")
    assert final_response.status_code == 200
    final_data = final_response.json()
    assert final_data["transcription_session_id"] == transcription_ids[-1]
    assert final_data["notes"] == "Updated with transcription 3"


def test_concurrent_session_access_persistence(authenticated_client, coaching_session_id):
    """Test persistence with concurrent-like access patterns."""

    # Create transcription session
    transcription_response = authenticated_client.post(
        "/sessions",
        json={
            "title": "Concurrent Access Test",
            "language": "cmn-Hant-TW"
        }
    )
    assert transcription_response.status_code == 201
    transcription_id = transcription_response.json()["id"]

    # Update coaching session
    update_response = authenticated_client.patch(
        f"/api/v1/coaching-sessions/{coaching_session_id}",
        json={"transcription_session_id": transcription_id}
    )
    assert update_response.status_code == 200

    # Simulate multiple concurrent reads (like frontend refreshing)
    for i in range(5):
        response = authenticated_client.get(f"/api/v1/coaching-sessions/{coaching_session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["transcription_session_id"] == transcription_id
        assert data["transcription_session_id"] is not None


def test_error_rollback_behavior(authenticated_client, coaching_session_id):
    """Test that failed updates don't affect existing data."""

    # Set initial transcription session
    transcription_response = authenticated_client.post(
        "/sessions",
        json={
            "title": "Error Rollback Test",
            "language": "en-US"
        }
    )
    assert transcription_response.status_code == 201
    valid_transcription_id = transcription_response.json()["id"]

    update_response = authenticated_client.patch(
        f"/api/v1/coaching-sessions/{coaching_session_id}",
        json={"transcription_session_id": valid_transcription_id}
    )
    assert update_response.status_code == 200

    # Attempt invalid update (non-existent transcription session)
    invalid_id = str(uuid4())
    invalid_response = authenticated_client.patch(
        f"/api/v1/coaching-sessions/{coaching_session_id}",
        json={"transcription_session_id": invalid_id}
    )
    # This might succeed or fail depending on validation, but original data should remain

    # Verify original data is preserved
    check_response = authenticated_client.get(f"/api/v1/coaching-sessions/{coaching_session_id}")
    assert check_response.status_code == 200
    check_data = check_response.json()

    # Should still have the valid transcription ID, not the invalid one
    assert check_data["transcription_session_id"] == valid_transcription_id
    assert check_data["transcription_session_id"] != invalid_id


def test_transcription_session_relationship_integrity(authenticated_client, coaching_session_id):
    """Test that the relationship between coaching and transcription sessions is maintained."""

    # Create transcription session with specific properties
    transcription_response = authenticated_client.post(
        "/sessions",
        json={
            "title": "Relationship Integrity Test",
            "language": "cmn-Hant-TW",
            "stt_provider": "google"
        }
    )
    assert transcription_response.status_code == 201
    transcription_data = transcription_response.json()
    transcription_id = transcription_data["id"]

    # Link coaching session to transcription
    update_response = authenticated_client.patch(
        f"/api/v1/coaching-sessions/{coaching_session_id}",
        json={"transcription_session_id": transcription_id}
    )
    assert update_response.status_code == 200

    # Verify relationship from coaching session side
    coaching_response = authenticated_client.get(f"/api/v1/coaching-sessions/{coaching_session_id}")
    assert coaching_response.status_code == 200
    coaching_data = coaching_response.json()
    assert coaching_data["transcription_session_id"] == transcription_id

    # Verify transcription session still exists and has correct properties
    transcription_check = authenticated_client.get(f"/sessions/{transcription_id}")
    assert transcription_check.status_code == 200
    transcription_check_data = transcription_check.json()
    assert transcription_check_data["id"] == transcription_id
    assert transcription_check_data["title"] == "Relationship Integrity Test"
    assert transcription_check_data["language"] == "cmn-Hant-TW"

    # Verify the relationship persists across multiple requests
    for _ in range(3):
        coaching_recheck = authenticated_client.get(f"/api/v1/coaching-sessions/{coaching_session_id}")
        assert coaching_recheck.status_code == 200
        coaching_recheck_data = coaching_recheck.json()
        assert coaching_recheck_data["transcription_session_id"] == transcription_id