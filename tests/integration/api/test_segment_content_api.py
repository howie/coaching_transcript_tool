"""Integration tests for segment content update API endpoint."""

from uuid import uuid4

from coaching_assistant.core.models.session import Session, SessionStatus
from coaching_assistant.core.models.transcript import TranscriptSegment


class TestSegmentContentAPI:
    """Test segment content update API endpoint with full integration."""

    def setup_test_data(self, db_session, test_user):
        """Setup test data for segment content tests."""
        # Create transcription session
        session = Session(
            id=uuid4(),
            user_id=test_user.id,
            title="Test Segment Content Session",
            status=SessionStatus.COMPLETED,
            language="en-US",
            duration_seconds=300,
        )
        db_session.add(session)
        db_session.flush()

        # Create transcript segments
        segments = [
            TranscriptSegment(
                id=uuid4(),
                session_id=session.id,
                speaker_id=1,
                speaker_name="Speaker 1",
                start_sec=0.0,
                end_sec=5.0,
                content="Hello, welcome to the session.",
                confidence_score=0.95,
            ),
            TranscriptSegment(
                id=uuid4(),
                session_id=session.id,
                speaker_id=2,
                speaker_name="Speaker 2",
                start_sec=5.5,
                end_sec=10.0,
                content="Thank you for having me.",
                confidence_score=0.92,
            ),
        ]

        for segment in segments:
            db_session.add(segment)

        db_session.commit()
        return session, segments

    def test_update_segment_content_success(
        self, db_session, authenticated_client, test_user
    ):
        """Test successful segment content update."""
        session, segments = self.setup_test_data(db_session, test_user)

        # Update content for both segments
        update_data = {
            "segment_content": {
                str(segments[0].id): "Hello, welcome to our coaching session.",
                str(segments[1].id): "Thank you, I'm excited to be here.",
            }
        }

        response = authenticated_client.patch(
            f"/api/v1/sessions/{session.id}/segment-content",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Segment content updated successfully"
        assert data["session_id"] == str(session.id)
        assert data["segments_updated"] == 2

        # Verify content was actually updated in database
        db_session.refresh(segments[0])
        db_session.refresh(segments[1])
        assert segments[0].content == "Hello, welcome to our coaching session."
        assert segments[1].content == "Thank you, I'm excited to be here."

    def test_update_segment_content_partial_update(
        self, db_session, authenticated_client, test_user
    ):
        """Test updating only some segments."""
        session, segments = self.setup_test_data(db_session, test_user)

        # Update only first segment
        update_data = {
            "segment_content": {
                str(segments[0].id): "Updated first segment only.",
            }
        }

        response = authenticated_client.patch(
            f"/api/v1/sessions/{session.id}/segment-content",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["segments_updated"] == 1

        # Verify only first segment was updated
        db_session.refresh(segments[0])
        db_session.refresh(segments[1])
        assert segments[0].content == "Updated first segment only."
        assert segments[1].content == "Thank you for having me."  # unchanged

    def test_update_segment_content_empty_content_allowed(
        self, db_session, authenticated_client, test_user
    ):
        """Test that empty strings are allowed as content."""
        session, segments = self.setup_test_data(db_session, test_user)

        # Update with empty string
        update_data = {
            "segment_content": {
                str(segments[0].id): "",
            }
        }

        response = authenticated_client.patch(
            f"/api/v1/sessions/{session.id}/segment-content",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["segments_updated"] == 1

        # Verify content was updated to empty string
        db_session.refresh(segments[0])
        assert segments[0].content == ""

    def test_update_segment_content_no_content_provided(
        self, db_session, authenticated_client, test_user
    ):
        """Test error when no segment content is provided."""
        session, _ = self.setup_test_data(db_session, test_user)

        update_data = {"segment_content": {}}

        response = authenticated_client.patch(
            f"/api/v1/sessions/{session.id}/segment-content",
            json=update_data,
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "No segment content provided"

    def test_update_segment_content_invalid_segment_id(
        self, db_session, authenticated_client, test_user
    ):
        """Test error with invalid segment ID."""
        session, _ = self.setup_test_data(db_session, test_user)

        update_data = {
            "segment_content": {
                "invalid-uuid": "Updated content",
            }
        }

        response = authenticated_client.patch(
            f"/api/v1/sessions/{session.id}/segment-content",
            json=update_data,
        )

        assert response.status_code == 400
        assert "Invalid segment ID format" in response.json()["detail"]

    def test_update_segment_content_nonexistent_segment(
        self, db_session, authenticated_client, test_user
    ):
        """Test error with non-existent segment ID."""
        session, _ = self.setup_test_data(db_session, test_user)

        nonexistent_id = str(uuid4())
        update_data = {
            "segment_content": {
                nonexistent_id: "Updated content",
            }
        }

        response = authenticated_client.patch(
            f"/api/v1/sessions/{session.id}/segment-content",
            json=update_data,
        )

        assert response.status_code == 404
        assert f"Segment not found: {nonexistent_id}" in response.json()["detail"]

    def test_update_segment_content_session_not_found(self, authenticated_client):
        """Test error when session doesn't exist."""
        nonexistent_session_id = uuid4()
        update_data = {
            "segment_content": {
                str(uuid4()): "Updated content",
            }
        }

        response = authenticated_client.patch(
            f"/api/v1/sessions/{nonexistent_session_id}/segment-content",
            json=update_data,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Session not found"

    def test_update_segment_content_access_denied(
        self, db_session, authenticated_client, test_user
    ):
        """Test access denied when updating another user's session."""
        from coaching_assistant.core.models.user import User

        # Create another user and their session
        other_user = User(
            id=uuid4(),
            email="other@example.com",
            hashed_password="hashed",
            is_active=True,
        )
        db_session.add(other_user)

        session = Session(
            id=uuid4(),
            user_id=other_user.id,  # Different user
            title="Other User Session",
            status=SessionStatus.COMPLETED,
            language="en-US",
            duration_seconds=300,
        )
        db_session.add(session)

        segment = TranscriptSegment(
            id=uuid4(),
            session_id=session.id,
            speaker_id=1,
            speaker_name="Speaker 1",
            start_sec=0.0,
            end_sec=5.0,
            content="Original content",
            confidence_score=0.95,
        )
        db_session.add(segment)
        db_session.commit()

        update_data = {
            "segment_content": {
                str(segment.id): "Malicious update",
            }
        }

        response = authenticated_client.patch(
            f"/api/v1/sessions/{session.id}/segment-content",
            json=update_data,
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Access denied"

    def test_update_segment_content_requires_completed_session(
        self, db_session, authenticated_client, test_user
    ):
        """Test error when trying to update non-completed session."""
        # Create session that's not completed
        session = Session(
            id=uuid4(),
            user_id=test_user.id,
            title="In Progress Session",
            status=SessionStatus.TRANSCRIBING,  # Not completed
            language="en-US",
            duration_seconds=300,
        )
        db_session.add(session)

        segment = TranscriptSegment(
            id=uuid4(),
            session_id=session.id,
            speaker_id=1,
            speaker_name="Speaker 1",
            start_sec=0.0,
            end_sec=5.0,
            content="Original content",
            confidence_score=0.95,
        )
        db_session.add(segment)
        db_session.commit()

        update_data = {
            "segment_content": {
                str(segment.id): "Updated content",
            }
        }

        response = authenticated_client.patch(
            f"/api/v1/sessions/{session.id}/segment-content",
            json=update_data,
        )

        assert response.status_code == 400
        assert "Cannot update segment content" in response.json()["detail"]
        assert "TRANSCRIBING" in response.json()["detail"]

    def test_update_segment_content_unauthenticated(
        self, client, db_session, test_user
    ):
        """Test that unauthenticated requests are rejected."""
        session, segments = self.setup_test_data(db_session, test_user)

        update_data = {
            "segment_content": {
                str(segments[0].id): "Should fail",
            }
        }

        response = client.patch(
            f"/api/v1/sessions/{session.id}/segment-content",
            json=update_data,
        )

        assert response.status_code == 401

    def test_update_segment_content_large_content(
        self, db_session, authenticated_client, test_user
    ):
        """Test updating with very large content."""
        session, segments = self.setup_test_data(db_session, test_user)

        # Create large content (10KB)
        large_content = "A" * 10240

        update_data = {
            "segment_content": {
                str(segments[0].id): large_content,
            }
        }

        response = authenticated_client.patch(
            f"/api/v1/sessions/{session.id}/segment-content",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["segments_updated"] == 1

        # Verify large content was stored
        db_session.refresh(segments[0])
        assert len(segments[0].content) == 10240
        assert segments[0].content == large_content

    def test_update_segment_content_special_characters(
        self, db_session, authenticated_client, test_user
    ):
        """Test updating with special characters and unicode."""
        session, segments = self.setup_test_data(db_session, test_user)

        special_content = "Hello 👋 世界! Special chars: @#$%^&*()[]{}|;':\",./<>?"

        update_data = {
            "segment_content": {
                str(segments[0].id): special_content,
            }
        }

        response = authenticated_client.patch(
            f"/api/v1/sessions/{session.id}/segment-content",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["segments_updated"] == 1

        # Verify special characters were preserved
        db_session.refresh(segments[0])
        assert segments[0].content == special_content
