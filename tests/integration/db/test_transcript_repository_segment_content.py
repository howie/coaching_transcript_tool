"""Integration tests for transcript repository segment content operations."""

import pytest
from uuid import uuid4
from sqlalchemy.exc import IntegrityError

from coaching_assistant.core.models.session import Session, SessionStatus
from coaching_assistant.core.models.transcript import TranscriptSegment
from coaching_assistant.infrastructure.db.repositories.transcript_repository import SQLAlchemyTranscriptRepository


class TestTranscriptRepositorySegmentContent:
    """Test transcript repository segment content persistence operations."""

    @pytest.fixture
    def transcript_repo(self, db_session):
        """Create transcript repository instance."""
        return SQLAlchemyTranscriptRepository(db_session)

    @pytest.fixture
    def test_session(self, db_session, test_user):
        """Create a test session."""
        session = Session(
            id=uuid4(),
            user_id=test_user.id,
            title="Test Session",
            status=SessionStatus.COMPLETED,
            language="en-US",
            duration_seconds=300,
        )
        db_session.add(session)
        db_session.commit()
        return session

    @pytest.fixture
    def test_segments(self, db_session, test_session):
        """Create test transcript segments."""
        segments = [
            TranscriptSegment(
                id=uuid4(),
                session_id=test_session.id,
                speaker_id=1,
                speaker_name="Speaker 1",
                start_sec=0.0,
                end_sec=5.0,
                content="Original content 1",
                confidence_score=0.95,
            ),
            TranscriptSegment(
                id=uuid4(),
                session_id=test_session.id,
                speaker_id=2,
                speaker_name="Speaker 2",
                start_sec=5.5,
                end_sec=10.0,
                content="Original content 2",
                confidence_score=0.92,
            ),
            TranscriptSegment(
                id=uuid4(),
                session_id=test_session.id,
                speaker_id=1,
                speaker_name="Speaker 1",
                start_sec=10.5,
                end_sec=15.0,
                content="Original content 3",
                confidence_score=0.88,
            ),
        ]

        for segment in segments:
            db_session.add(segment)

        db_session.commit()
        return segments

    def test_get_segments_by_session_id(self, transcript_repo, test_session, test_segments):
        """Test retrieving segments by session ID."""
        segments = transcript_repo.get_segments_by_session_id(test_session.id)

        assert len(segments) == 3
        segment_contents = [s.content for s in segments]
        assert "Original content 1" in segment_contents
        assert "Original content 2" in segment_contents
        assert "Original content 3" in segment_contents

    def test_get_segment_by_id(self, transcript_repo, test_segments):
        """Test retrieving individual segment by ID."""
        segment = transcript_repo.get_segment_by_id(test_segments[0].id)

        assert segment is not None
        assert segment.id == test_segments[0].id
        assert segment.content == "Original content 1"

    def test_get_segment_by_id_not_found(self, transcript_repo):
        """Test retrieving non-existent segment."""
        segment = transcript_repo.get_segment_by_id(uuid4())
        assert segment is None

    def test_update_segment_content_single(self, transcript_repo, db_session, test_segments):
        """Test updating content of a single segment."""
        segment_id = test_segments[0].id
        new_content = "Updated content for segment 1"

        # Update the segment content
        segment = transcript_repo.get_segment_by_id(segment_id)
        segment.content = new_content

        # In a real repository, there would be an update method
        # For now, we test the persistence directly
        db_session.commit()

        # Verify the update persisted
        updated_segment = transcript_repo.get_segment_by_id(segment_id)
        assert updated_segment.content == new_content

        # Verify other segments unchanged
        other_segment = transcript_repo.get_segment_by_id(test_segments[1].id)
        assert other_segment.content == "Original content 2"

    def test_update_segment_content_multiple(self, transcript_repo, db_session, test_segments):
        """Test updating content of multiple segments in single transaction."""
        updates = [
            (test_segments[0].id, "Bulk update 1"),
            (test_segments[2].id, "Bulk update 3"),
        ]

        # Update multiple segments
        for segment_id, new_content in updates:
            segment = transcript_repo.get_segment_by_id(segment_id)
            segment.content = new_content

        db_session.commit()

        # Verify all updates persisted
        updated_segment_1 = transcript_repo.get_segment_by_id(test_segments[0].id)
        assert updated_segment_1.content == "Bulk update 1"

        updated_segment_3 = transcript_repo.get_segment_by_id(test_segments[2].id)
        assert updated_segment_3.content == "Bulk update 3"

        # Verify unchanged segment
        unchanged_segment = transcript_repo.get_segment_by_id(test_segments[1].id)
        assert unchanged_segment.content == "Original content 2"

    def test_update_segment_content_empty_string(self, transcript_repo, db_session, test_segments):
        """Test updating segment content to empty string."""
        segment_id = test_segments[0].id

        segment = transcript_repo.get_segment_by_id(segment_id)
        segment.content = ""
        db_session.commit()

        # Verify empty string is preserved
        updated_segment = transcript_repo.get_segment_by_id(segment_id)
        assert updated_segment.content == ""

    def test_update_segment_content_very_long(self, transcript_repo, db_session, test_segments):
        """Test updating segment with very long content."""
        segment_id = test_segments[0].id
        long_content = "A" * 50000  # 50KB content

        segment = transcript_repo.get_segment_by_id(segment_id)
        segment.content = long_content
        db_session.commit()

        # Verify long content is preserved
        updated_segment = transcript_repo.get_segment_by_id(segment_id)
        assert len(updated_segment.content) == 50000
        assert updated_segment.content == long_content

    def test_update_segment_content_unicode(self, transcript_repo, db_session, test_segments):
        """Test updating segment with unicode characters."""
        segment_id = test_segments[0].id
        unicode_content = "Hello 👋 世界! Émojis and spéciàl châràctërs: ñüñéz"

        segment = transcript_repo.get_segment_by_id(segment_id)
        segment.content = unicode_content
        db_session.commit()

        # Verify unicode content is preserved
        updated_segment = transcript_repo.get_segment_by_id(segment_id)
        assert updated_segment.content == unicode_content

    def test_update_segment_content_transaction_rollback(self, transcript_repo, db_session, test_segments):
        """Test that failed updates don't partially commit."""
        original_content_1 = test_segments[0].content
        original_content_2 = test_segments[1].content

        try:
            # Start transaction
            segment_1 = transcript_repo.get_segment_by_id(test_segments[0].id)
            segment_1.content = "Updated content 1"

            # This should succeed
            db_session.flush()

            # Simulate an error that would cause rollback
            segment_2 = transcript_repo.get_segment_by_id(test_segments[1].id)
            segment_2.content = None  # This might cause an error depending on constraints

            # This should fail if content is NOT NULL
            db_session.commit()

        except Exception:
            # Rollback should have occurred
            db_session.rollback()

        # Verify neither update persisted
        segment_1 = transcript_repo.get_segment_by_id(test_segments[0].id)
        segment_2 = transcript_repo.get_segment_by_id(test_segments[1].id)

        assert segment_1.content == original_content_1
        assert segment_2.content == original_content_2

    def test_segment_content_concurrency(self, transcript_repo, db_session, test_segments):
        """Test handling of concurrent segment content updates."""
        segment_id = test_segments[0].id

        # Simulate concurrent access by getting the same segment in two "sessions"
        segment_1 = transcript_repo.get_segment_by_id(segment_id)
        segment_2 = transcript_repo.get_segment_by_id(segment_id)

        # Update in first "session"
        segment_1.content = "First update"
        db_session.commit()

        # Update in second "session" (should overwrite)
        db_session.refresh(segment_2)  # Refresh to get latest
        segment_2.content = "Second update"
        db_session.commit()

        # Verify final state
        final_segment = transcript_repo.get_segment_by_id(segment_id)
        assert final_segment.content == "Second update"

    def test_segment_content_with_metadata_preservation(self, transcript_repo, db_session, test_segments):
        """Test that updating content preserves other segment metadata."""
        segment_id = test_segments[0].id
        original_segment = transcript_repo.get_segment_by_id(segment_id)

        # Store original metadata
        original_speaker_id = original_segment.speaker_id
        original_start_sec = original_segment.start_sec
        original_end_sec = original_segment.end_sec
        original_confidence = original_segment.confidence_score

        # Update only content
        original_segment.content = "Content updated, metadata should remain"
        db_session.commit()

        # Verify metadata is preserved
        updated_segment = transcript_repo.get_segment_by_id(segment_id)
        assert updated_segment.content == "Content updated, metadata should remain"
        assert updated_segment.speaker_id == original_speaker_id
        assert updated_segment.start_sec == original_start_sec
        assert updated_segment.end_sec == original_end_sec
        assert updated_segment.confidence_score == original_confidence

    def test_segment_ordering_preserved_after_content_update(self, transcript_repo, db_session, test_session, test_segments):
        """Test that segment ordering is preserved after content updates."""
        # Update all segments in reverse order
        for i, segment in enumerate(reversed(test_segments)):
            segment.content = f"Reordered content {i}"

        db_session.commit()

        # Retrieve segments and verify ordering is still by time
        segments = transcript_repo.get_segments_by_session_id(test_session.id)

        # Should still be ordered by start_sec
        assert len(segments) == 3
        assert segments[0].start_sec == 0.0
        assert segments[1].start_sec == 5.5
        assert segments[2].start_sec == 10.5

        # But content should reflect the updates
        assert segments[2].content == "Reordered content 0"  # Last segment updated first
        assert segments[1].content == "Reordered content 1"  # Middle segment
        assert segments[0].content == "Reordered content 2"  # First segment updated last

    def test_segment_content_search_after_update(self, transcript_repo, db_session, test_session, test_segments):
        """Test that segment content can be searched after updates."""
        # Update segments with searchable content
        test_segments[0].content = "The coaching session was very productive"
        test_segments[1].content = "We discussed leadership and management skills"
        test_segments[2].content = "Next steps include practice and feedback"

        db_session.commit()

        # Retrieve all segments and search
        segments = transcript_repo.get_segments_by_session_id(test_session.id)

        # Find segments containing specific words
        coaching_segments = [s for s in segments if "coaching" in s.content.lower()]
        leadership_segments = [s for s in segments if "leadership" in s.content.lower()]
        practice_segments = [s for s in segments if "practice" in s.content.lower()]

        assert len(coaching_segments) == 1
        assert len(leadership_segments) == 1
        assert len(practice_segments) == 1

        assert coaching_segments[0].speaker_id == 1
        assert leadership_segments[0].speaker_id == 2
        assert practice_segments[0].speaker_id == 1