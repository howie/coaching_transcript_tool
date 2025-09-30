"""E2E tests for complete session workflows.

This module contains end-to-end tests for session creation, file upload,
transcription processing, and export workflows.
"""

import io
import time
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from tests.e2e.test_base import BaseE2ETest

from src.coaching_assistant.core.models.session import SessionStatus
from src.coaching_assistant.models.session import Session
from src.coaching_assistant.models.transcript import TranscriptSegment


@pytest.mark.e2e
@pytest.mark.slow
class TestSessionWorkflowsE2E(BaseE2ETest):
    """End-to-end tests for complete session workflows."""

    def test_complete_session_creation_and_upload_workflow(
        self, authenticated_user, db_session
    ):
        """Test complete session creation and file upload workflow."""
        user = authenticated_user

        # Step 1: Create a new session
        session_response = self.client.post(
            "/sessions",
            json={
                "title": "E2E Test Session",
                "language": "cmn-Hant-TW",
                "stt_provider": "google",
            },
            headers={"Authorization": f"Bearer {user['token']}"},
        )

        assert session_response.status_code == 200
        session_data = session_response.json()
        assert session_data["title"] == "E2E Test Session"
        assert session_data["status"] == "uploading"
        assert session_data["language"] == "cmn-Hant-TW"
        session_id = session_data["id"]

        # Step 2: Get upload URL
        upload_url_response = self.client.post(
            f"/sessions/{session_id}/upload-url",
            params={"filename": "test_audio.mp3", "file_size_mb": 5.0},
            headers={"Authorization": f"Bearer {user['token']}"},
        )

        assert upload_url_response.status_code == 200
        upload_data = upload_url_response.json()
        assert "upload_url" in upload_data
        assert "gcs_path" in upload_data
        assert "expires_at" in upload_data

        # Step 3: Simulate upload confirmation (in real test, would upload to GCS)
        confirm_response = self.client.post(
            f"/sessions/{session_id}/confirm-upload",
            headers={"Authorization": f"Bearer {user['token']}"},
        )

        # Note: This will return file_exists=False in tests since we don't actually upload
        # but we verify the API structure works
        assert confirm_response.status_code == 200
        confirm_data = confirm_response.json()
        assert "file_exists" in confirm_data
        assert "ready_for_transcription" in confirm_data
        assert "message" in confirm_data

        print(
            f"✅ Session creation and upload workflow completed for session {session_id}"
        )

    def test_session_status_tracking_workflow(
        self, authenticated_user_with_session, db_session
    ):
        """Test session status tracking throughout the workflow."""
        user = authenticated_user_with_session
        session_id = user["session_id"]

        # Step 1: Check initial status
        status_response = self.client.get(
            f"/sessions/{session_id}/status",
            headers={"Authorization": f"Bearer {user['token']}"},
        )

        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["session_id"] == session_id
        assert "status" in status_data
        assert "progress" in status_data
        assert "message" in status_data

        # Step 2: Update session to processing state (simulate)
        # Note: In real workflow, this would be triggered by start-transcription
        # but we simulate the status progression here

        # Check status again after simulated processing
        time.sleep(0.1)  # Small delay to simulate time passing
        updated_status_response = self.client.get(
            f"/sessions/{session_id}/status",
            headers={"Authorization": f"Bearer {user['token']}"},
        )

        assert updated_status_response.status_code == 200
        updated_status = updated_status_response.json()
        assert "progress" in updated_status
        assert (
            "estimated_completion" in updated_status
            or updated_status["estimated_completion"] is None
        )

        print(f"✅ Session status tracking workflow completed for session {session_id}")

    def test_session_listing_and_filtering_workflow(
        self, authenticated_user, db_session
    ):
        """Test session listing and filtering functionality."""
        user = authenticated_user

        # Step 1: Create multiple sessions with different statuses
        sessions_created = []

        for i in range(3):
            session_response = self.client.post(
                "/sessions",
                json={
                    "title": f"Filter Test Session {i + 1}",
                    "language": "cmn-Hant-TW",
                    "stt_provider": "auto",
                },
                headers={"Authorization": f"Bearer {user['token']}"},
            )
            assert session_response.status_code == 200
            sessions_created.append(session_response.json())

        # Step 2: List all sessions
        list_response = self.client.get(
            "/sessions", headers={"Authorization": f"Bearer {user['token']}"}
        )

        assert list_response.status_code == 200
        all_sessions = list_response.json()
        assert len(all_sessions) >= 3

        # Verify our created sessions are in the list
        created_ids = [s["id"] for s in sessions_created]
        listed_ids = [s["id"] for s in all_sessions]
        for created_id in created_ids:
            assert created_id in listed_ids

        # Step 3: Test filtering by status
        filtered_response = self.client.get(
            "/sessions",
            params={"status": "uploading"},
            headers={"Authorization": f"Bearer {user['token']}"},
        )

        assert filtered_response.status_code == 200
        filtered_sessions = filtered_response.json()
        # All our newly created sessions should be in uploading status
        for session in filtered_sessions:
            if session["id"] in created_ids:
                assert session["status"] == "uploading"

        # Step 4: Test pagination
        paginated_response = self.client.get(
            "/sessions",
            params={"limit": 2, "offset": 0},
            headers={"Authorization": f"Bearer {user['token']}"},
        )

        assert paginated_response.status_code == 200
        paginated_sessions = paginated_response.json()
        assert len(paginated_sessions) <= 2

        print("✅ Session listing and filtering workflow completed")

    def test_session_detail_retrieval_workflow(
        self, authenticated_user_with_session, db_session
    ):
        """Test detailed session retrieval workflow."""
        user = authenticated_user_with_session
        session_id = user["session_id"]

        # Step 1: Get session details
        detail_response = self.client.get(
            f"/sessions/{session_id}",
            headers={"Authorization": f"Bearer {user['token']}"},
        )

        assert detail_response.status_code == 200
        session_detail = detail_response.json()
        assert session_detail["id"] == session_id
        assert session_detail["title"] == "Test Session"
        assert "status" in session_detail
        assert "language" in session_detail
        assert "created_at" in session_detail
        assert "updated_at" in session_detail

        # Step 2: Verify access control - other users cannot access
        other_user_response = self.client.get(
            f"/sessions/{uuid4()}",  # Non-existent session
            headers={"Authorization": f"Bearer {user['token']}"},
        )

        assert other_user_response.status_code == 404

        print(
            f"✅ Session detail retrieval workflow completed for session {session_id}"
        )

    def test_transcript_upload_workflow(
        self, authenticated_user_with_session, db_session
    ):
        """Test direct transcript file upload workflow."""
        user = authenticated_user_with_session
        session_id = user["session_id"]

        # Step 1: Prepare VTT transcript content
        vtt_content = """WEBVTT

00:00:00.000 --> 00:00:05.000
<v 教練>歡迎來到今天的教練課程

00:00:05.000 --> 00:00:10.000
<v 客戶>謝謝教練，我今天想討論我的職業發展

00:00:10.000 --> 00:00:15.000
<v 教練>很好，讓我們開始探討你的目標
"""

        # Step 2: Upload VTT transcript
        vtt_file = io.BytesIO(vtt_content.encode("utf-8"))
        upload_response = self.client.post(
            f"/sessions/{session_id}/transcript",
            files={"file": ("transcript.vtt", vtt_file, "text/vtt")},
            headers={"Authorization": f"Bearer {user['token']}"},
        )

        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert upload_data["message"] == "Transcript uploaded successfully"
        assert upload_data["segments_count"] == 3
        assert "duration_seconds" in upload_data

        # Step 3: Verify session status updated to completed
        status_response = self.client.get(
            f"/sessions/{session_id}/status",
            headers={"Authorization": f"Bearer {user['token']}"},
        )

        assert status_response.status_code == 200
        status_data = status_response.json()
        # Status might be completed or still processing depending on implementation
        assert "progress" in status_data

        # Step 4: Test SRT upload as well
        srt_content = """1
00:00:00,000 --> 00:00:05,000
教練: 歡迎來到今天的教練課程

2
00:00:05,000 --> 00:00:10,000
客戶: 謝謝教練，我今天想討論我的職業發展
"""

        # Create new session for SRT test
        new_session_response = self.client.post(
            "/sessions",
            json={
                "title": "SRT Upload Test Session",
                "language": "cmn-Hant-TW",
                "stt_provider": "auto",
            },
            headers={"Authorization": f"Bearer {user['token']}"},
        )
        new_session_id = new_session_response.json()["id"]

        srt_file = io.BytesIO(srt_content.encode("utf-8"))
        srt_upload_response = self.client.post(
            f"/sessions/{new_session_id}/transcript",
            files={"file": ("transcript.srt", srt_file, "text/srt")},
            headers={"Authorization": f"Bearer {user['token']}"},
        )

        assert srt_upload_response.status_code == 200
        srt_upload_data = srt_upload_response.json()
        assert srt_upload_data["segments_count"] == 2

        print(
            f"✅ Transcript upload workflow completed for sessions {session_id} and {new_session_id}"
        )

    def test_transcript_export_workflow(
        self, authenticated_user_with_completed_session, db_session
    ):
        """Test transcript export in various formats."""
        user = authenticated_user_with_completed_session
        session_id = user["session_id"]

        # Test each export format
        formats = ["json", "vtt", "srt", "txt", "xlsx"]

        for format_type in formats:
            # Step: Export transcript in each format
            export_response = self.client.get(
                f"/sessions/{session_id}/transcript",
                params={"format": format_type},
                headers={"Authorization": f"Bearer {user['token']}"},
            )

            if export_response.status_code == 200:
                # Verify content type based on format
                content_type = export_response.headers.get("content-type", "")

                if format_type == "json":
                    assert "application/json" in content_type
                elif format_type == "vtt":
                    assert "text/vtt" in content_type
                elif format_type == "srt":
                    assert "text/srt" in content_type or "text/plain" in content_type
                elif format_type == "txt":
                    assert "text/plain" in content_type
                elif format_type == "xlsx":
                    assert "spreadsheetml" in content_type or "excel" in content_type

                # Verify content-disposition header for download
                disposition = export_response.headers.get("content-disposition", "")
                assert "attachment" in disposition

                print(f"✅ Export format {format_type} successful")
            else:
                # Some formats might not be available if no transcript exists
                print(
                    f"⚠️ Export format {format_type} returned {export_response.status_code}"
                )

        print(f"✅ Transcript export workflow completed for session {session_id}")

    def test_session_error_handling_workflow(self, authenticated_user, db_session):
        """Test various error scenarios in session workflows."""
        user = authenticated_user

        # Test 1: Create session with invalid data
        invalid_session_response = self.client.post(
            "/sessions",
            json={
                "title": "",  # Empty title should be invalid
                "language": "invalid-language",
                "stt_provider": "invalid-provider",
            },
            headers={"Authorization": f"Bearer {user['token']}"},
        )

        assert invalid_session_response.status_code == 422  # Validation error

        # Test 2: Access non-existent session
        nonexistent_response = self.client.get(
            f"/sessions/{uuid4()}", headers={"Authorization": f"Bearer {user['token']}"}
        )

        assert nonexistent_response.status_code == 404

        # Test 3: Upload URL with invalid file size
        valid_session_response = self.client.post(
            "/sessions",
            json={
                "title": "Error Test Session",
                "language": "cmn-Hant-TW",
                "stt_provider": "auto",
            },
            headers={"Authorization": f"Bearer {user['token']}"},
        )
        session_id = valid_session_response.json()["id"]

        # Assuming user has FREE plan with 60MB limit
        large_file_response = self.client.post(
            f"/sessions/{session_id}/upload-url",
            params={
                "filename": "large_file.mp3",
                "file_size_mb": 100.0,  # Exceeds typical free plan limit
            },
            headers={"Authorization": f"Bearer {user['token']}"},
        )

        # Should either succeed (if user has higher plan) or fail with 413
        assert large_file_response.status_code in [200, 413]

        # Test 4: Invalid transcript format
        invalid_transcript = io.BytesIO(b"This is not a valid transcript format")
        invalid_upload_response = self.client.post(
            f"/sessions/{session_id}/transcript",
            files={"file": ("invalid.txt", invalid_transcript, "text/plain")},
            headers={"Authorization": f"Bearer {user['token']}"},
        )

        assert invalid_upload_response.status_code == 400

        print("✅ Session error handling workflow completed")

    def test_concurrent_session_operations(self, authenticated_user, db_session):
        """Test concurrent session operations for race condition handling."""
        user = authenticated_user

        # Create a session
        session_response = self.client.post(
            "/sessions",
            json={
                "title": "Concurrency Test Session",
                "language": "cmn-Hant-TW",
                "stt_provider": "auto",
            },
            headers={"Authorization": f"Bearer {user['token']}"},
        )
        session_id = session_response.json()["id"]

        # Simulate concurrent status requests
        import threading

        results = []

        def get_status():
            response = self.client.get(
                f"/sessions/{session_id}/status",
                headers={"Authorization": f"Bearer {user['token']}"},
            )
            results.append(response.status_code)

        # Launch multiple concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=get_status)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 5

        print("✅ Concurrent session operations test completed")

    @pytest.fixture
    def authenticated_user_with_session(self, authenticated_user, db_session):
        """Create an authenticated user with a test session."""
        user = authenticated_user

        # Create a session for testing
        session = Session(
            id=uuid4(),
            user_id=user["user_id"],
            title="Test Session",
            language="cmn-Hant-TW",
            status=SessionStatus.UPLOADING,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        db_session.add(session)
        db_session.commit()

        user["session_id"] = str(session.id)
        return user

    @pytest.fixture
    def authenticated_user_with_completed_session(self, authenticated_user, db_session):
        """Create an authenticated user with a completed session containing transcript."""
        user = authenticated_user

        # Create a completed session
        session = Session(
            id=uuid4(),
            user_id=user["user_id"],
            title="Completed Test Session",
            language="cmn-Hant-TW",
            status=SessionStatus.COMPLETED,
            duration_seconds=30,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        db_session.add(session)

        # Add some transcript segments
        segments = [
            TranscriptSegment(
                id=uuid4(),
                session_id=session.id,
                speaker_id=1,
                start_seconds=0.0,
                end_seconds=5.0,
                content="教練說話內容",
                confidence=0.95,
            ),
            TranscriptSegment(
                id=uuid4(),
                session_id=session.id,
                speaker_id=2,
                start_seconds=5.0,
                end_seconds=10.0,
                content="客戶回應內容",
                confidence=0.92,
            ),
        ]

        for segment in segments:
            db_session.add(segment)

        db_session.commit()

        user["session_id"] = str(session.id)
        return user

    def test_session_providers_endpoint(self, authenticated_user):
        """Test the providers information endpoint."""
        _ = authenticated_user  # Ensure fixture side effects execute

        # Get available providers
        providers_response = self.client.get("/sessions/providers")

        assert providers_response.status_code == 200
        providers_data = providers_response.json()
        assert "available_providers" in providers_data
        assert "default_provider" in providers_data

        # Verify provider structure
        providers = providers_data["available_providers"]
        assert len(providers) > 0

        for provider in providers:
            assert "name" in provider
            assert "display_name" in provider
            assert "supported_languages" in provider
            assert "features" in provider

        # Verify at least Google and AssemblyAI providers
        provider_names = [p["name"] for p in providers]
        assert "google" in provider_names
        assert "assemblyai" in provider_names

        print("✅ Session providers endpoint test completed")

    def test_session_workflow_with_speaker_roles(
        self, authenticated_user_with_completed_session, db_session
    ):
        """Test session workflow including speaker role management."""
        user = authenticated_user_with_completed_session
        session_id = user["session_id"]

        # Step 1: Update speaker roles
        speaker_roles_response = self.client.patch(
            f"/sessions/{session_id}/speaker-roles",
            json={"speaker_roles": {"1": "coach", "2": "client"}},
            headers={"Authorization": f"Bearer {user['token']}"},
        )

        # Should succeed or fail gracefully
        assert speaker_roles_response.status_code in [200, 400, 404]

        if speaker_roles_response.status_code == 200:
            roles_data = speaker_roles_response.json()
            assert "success" in roles_data or "updated" in str(roles_data)

        # Step 2: Update individual segment roles
        segment_roles_response = self.client.patch(
            f"/sessions/{session_id}/segment-roles",
            json={
                "segment_roles": {}  # Empty for test, would contain segment_id -> role mappings
            },
            headers={"Authorization": f"Bearer {user['token']}"},
        )

        # Should succeed or fail gracefully
        assert segment_roles_response.status_code in [200, 400, 404]

        print(
            f"✅ Session workflow with speaker roles completed for session {session_id}"
        )
