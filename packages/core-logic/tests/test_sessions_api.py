"""Tests for sessions API endpoints."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from fastapi.testclient import TestClient
from datetime import datetime

from coaching_assistant.main import app
from coaching_assistant.models.session import Session, SessionStatus
from coaching_assistant.models.user import User
from coaching_assistant.models.transcript import TranscriptSegment


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_session():
    """Create a mock session."""
    session = Mock(spec=Session)
    session.id = uuid4()
    session.title = "Test Session"
    session.status = SessionStatus.UPLOADING
    session.language = "zh-TW"
    session.audio_filename = None
    session.duration_sec = None
    session.duration_minutes = 0.0
    session.segments_count = 0
    session.error_message = None
    session.stt_cost_usd = None
    session.created_at = datetime.utcnow()
    session.updated_at = datetime.utcnow()
    session.gcs_audio_path = None
    return session


class TestSessionsAPI:
    """Test sessions API endpoints."""
    
    @patch('coaching_assistant.api.sessions.get_current_user_dependency')
    @patch('coaching_assistant.api.sessions.get_db')
    def test_create_session(self, mock_get_db, mock_get_user, client, mock_user):
        """Test creating a new session."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_user
        
        # Mock database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        response = client.post(
            "/api/v1/sessions",
            json={
                "title": "Test Session",
                "language": "zh-TW"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Session"
        assert data["language"] == "zh-TW"
        assert data["status"] == "uploading"
    
    @patch('coaching_assistant.api.sessions.get_current_user_dependency')
    @patch('coaching_assistant.api.sessions.get_db')
    def test_list_sessions(self, mock_get_db, mock_get_user, client, mock_user, mock_session):
        """Test listing sessions."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_user
        
        # Mock query chain
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_session]
        mock_db.query.return_value = mock_query
        
        response = client.get("/api/v1/sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Session"
    
    @patch('coaching_assistant.api.sessions.get_current_user_dependency')
    @patch('coaching_assistant.api.sessions.get_db')
    def test_get_session(self, mock_get_db, mock_get_user, client, mock_user, mock_session):
        """Test getting a specific session."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_user
        
        # Mock query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_session
        mock_db.query.return_value = mock_query
        
        response = client.get(f"/api/v1/sessions/{mock_session.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Session"
        assert data["id"] == str(mock_session.id)
    
    @patch('coaching_assistant.api.sessions.get_current_user_dependency')
    @patch('coaching_assistant.api.sessions.get_db')
    def test_get_session_not_found(self, mock_get_db, mock_get_user, client, mock_user):
        """Test getting non-existent session."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_user
        
        # Mock query returning None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        response = client.get(f"/api/v1/sessions/{uuid4()}")
        
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]
    
    @patch('coaching_assistant.api.sessions.get_current_user_dependency')
    @patch('coaching_assistant.api.sessions.get_db')
    @patch('coaching_assistant.api.sessions.GCSUploader')
    @patch('coaching_assistant.api.sessions.settings')
    def test_get_upload_url(
        self, 
        mock_settings, 
        mock_uploader_class, 
        mock_get_db, 
        mock_get_user, 
        client, 
        mock_user, 
        mock_session
    ):
        """Test getting upload URL."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_user
        mock_settings.GOOGLE_STORAGE_BUCKET = "test-bucket"
        mock_settings.GOOGLE_APPLICATION_CREDENTIALS_JSON = "{}"
        
        # Mock session query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_session
        mock_db.query.return_value = mock_query
        
        # Mock uploader
        mock_uploader = Mock()
        mock_uploader.generate_signed_upload_url.return_value = (
            "https://storage.googleapis.com/upload-url", 
            datetime.utcnow()
        )
        mock_uploader_class.return_value = mock_uploader
        
        response = client.post(
            f"/api/v1/sessions/{mock_session.id}/upload-url?filename=test.mp3"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "upload_url" in data
        assert "gcs_path" in data
        assert "expires_at" in data
    
    @patch('coaching_assistant.api.sessions.get_current_user_dependency')
    @patch('coaching_assistant.api.sessions.get_db')
    @patch('coaching_assistant.api.sessions.transcribe_audio')
    def test_start_transcription(
        self, 
        mock_transcribe_task, 
        mock_get_db, 
        mock_get_user, 
        client, 
        mock_user, 
        mock_session
    ):
        """Test starting transcription."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_user
        
        # Setup session with uploaded audio
        mock_session.gcs_audio_path = "gs://test-bucket/test.mp3"
        mock_session.update_status = Mock()
        
        # Mock session query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_session
        mock_db.query.return_value = mock_query
        
        # Mock Celery task
        mock_task = Mock()
        mock_task.id = "task-123"
        mock_transcribe_task.delay.return_value = mock_task
        
        response = client.post(f"/api/v1/sessions/{mock_session.id}/start-transcription")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Transcription started"
        assert data["task_id"] == "task-123"
        
        # Verify transcription task was queued
        mock_transcribe_task.delay.assert_called_once_with(
            session_id=str(mock_session.id),
            gcs_uri="gs://test-bucket/test.mp3",
            language="zh-TW"
        )
    
    @patch('coaching_assistant.api.sessions.get_current_user_dependency')
    @patch('coaching_assistant.api.sessions.get_db')
    def test_export_transcript_json(
        self, 
        mock_get_db, 
        mock_get_user, 
        client, 
        mock_user
    ):
        """Test exporting transcript as JSON."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_get_user.return_value = mock_user
        
        # Create completed session
        session = Mock(spec=Session)
        session.id = uuid4()
        session.title = "Completed Session"
        session.status = SessionStatus.COMPLETED
        session.duration_sec = 60
        session.language = "zh-TW"
        session.created_at = datetime.utcnow()
        
        # Create mock segments
        segments = []
        for i in range(2):
            segment = Mock(spec=TranscriptSegment)
            segment.speaker_id = i + 1
            segment.start_sec = i * 5.0
            segment.end_sec = (i + 1) * 5.0
            segment.content = f"Segment {i + 1} content"
            segment.confidence = 0.95
            segments.append(segment)
        
        # Mock queries
        session_query = Mock()
        session_query.filter.return_value = session_query
        session_query.first.return_value = session
        
        segments_query = Mock()
        segments_query.filter.return_value = segments_query
        segments_query.order_by.return_value = segments_query
        segments_query.all.return_value = segments
        
        mock_db.query.side_effect = [session_query, segments_query]
        
        response = client.get(f"/api/v1/sessions/{session.id}/transcript?format=json")
        
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        
        # Parse JSON response
        import json
        data = json.loads(response.content)
        assert data["title"] == "Completed Session"
        assert len(data["segments"]) == 2
        assert data["segments"][0]["speaker_id"] == 1
        assert data["segments"][1]["speaker_id"] == 2