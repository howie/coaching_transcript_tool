"""Test transcript timestamps are correctly saved and retrieved."""

from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from coaching_assistant.models.base import Base
from coaching_assistant.models.transcript import TranscriptSegment
from coaching_assistant.models.session import Session, SessionStatus


def test_transcript_timestamps():
    """Test that transcript timestamps are correctly saved."""
    
    # Create in-memory database for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Create a test session
        session_id = uuid4()
        session = Session(
            id=session_id,
            user_id=uuid4(),
            title="Test Session",
            status=SessionStatus.COMPLETED,
            language="zh-TW",
            duration_sec=120
        )
        db.add(session)
        
        # Create test transcript segments with timestamps
        segments = [
            TranscriptSegment(
                session_id=session_id,
                speaker_id=1,
                start_sec=0.5,
                end_sec=5.3,
                content="這是第一段話",
                confidence=0.95
            ),
            TranscriptSegment(
                session_id=session_id,
                speaker_id=2,
                start_sec=5.8,
                end_sec=12.4,
                content="這是第二段話",
                confidence=0.92
            ),
            TranscriptSegment(
                session_id=session_id,
                speaker_id=1,
                start_sec=13.0,
                end_sec=20.5,
                content="這是第三段話",
                confidence=0.88
            )
        ]
        
        for segment in segments:
            db.add(segment)
        
        db.commit()
        
        # Query back the segments
        retrieved_segments = db.query(TranscriptSegment).filter(
            TranscriptSegment.session_id == session_id
        ).order_by(TranscriptSegment.start_sec).all()
        
        # Verify timestamps are preserved
        assert len(retrieved_segments) == 3
        
        # Check first segment
        assert retrieved_segments[0].start_sec == 0.5
        assert retrieved_segments[0].end_sec == 5.3
        assert retrieved_segments[0].content == "這是第一段話"
        
        # Check second segment
        assert retrieved_segments[1].start_sec == 5.8
        assert retrieved_segments[1].end_sec == 12.4
        assert retrieved_segments[1].content == "這是第二段話"
        
        # Check third segment
        assert retrieved_segments[2].start_sec == 13.0
        assert retrieved_segments[2].end_sec == 20.5
        assert retrieved_segments[2].content == "這是第三段話"
        
        print("✅ All timestamp tests passed!")
        print(f"Segment 1: {retrieved_segments[0].start_sec:.1f}s - {retrieved_segments[0].end_sec:.1f}s")
        print(f"Segment 2: {retrieved_segments[1].start_sec:.1f}s - {retrieved_segments[1].end_sec:.1f}s")
        print(f"Segment 3: {retrieved_segments[2].start_sec:.1f}s - {retrieved_segments[2].end_sec:.1f}s")
        
    finally:
        db.close()


if __name__ == "__main__":
    test_transcript_timestamps()