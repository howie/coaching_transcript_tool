"""Transcript repository implementation using SQLAlchemy."""

from typing import List, Dict
from uuid import UUID
from sqlalchemy.orm import Session

from ....core.repositories.ports import TranscriptRepoPort
from ....models.transcript import TranscriptSegment


class TranscriptRepository(TranscriptRepoPort):
    """SQLAlchemy implementation of TranscriptRepoPort."""

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_by_session_id(self, session_id: UUID) -> List[TranscriptSegment]:
        """Get all transcript segments for a session."""
        return (
            self.db_session.query(TranscriptSegment)
            .filter(TranscriptSegment.session_id == session_id)
            .order_by(TranscriptSegment.start_time)
            .all()
        )

    def save_segments(self, segments: List[TranscriptSegment]) -> List[TranscriptSegment]:
        """Save multiple transcript segments."""
        for segment in segments:
            self.db_session.add(segment)
        
        self.db_session.commit()
        
        # Refresh all segments
        for segment in segments:
            self.db_session.refresh(segment)
            
        return segments

    def update_speaker_roles(
        self, session_id: UUID, role_mappings: Dict[str, str]
    ) -> List[TranscriptSegment]:
        """Update speaker roles for session segments."""
        segments = self.get_by_session_id(session_id)
        
        updated_segments = []
        for segment in segments:
            if segment.speaker in role_mappings:
                segment.speaker_role = role_mappings[segment.speaker]
                updated_segments.append(segment)
        
        if updated_segments:
            self.db_session.commit()
            for segment in updated_segments:
                self.db_session.refresh(segment)
        
        return segments  # Return all segments, including unchanged ones

    def delete_by_session_id(self, session_id: UUID) -> bool:
        """Delete all segments for a session."""
        deleted_count = (
            self.db_session.query(TranscriptSegment)
            .filter(TranscriptSegment.session_id == session_id)
            .delete()
        )
        
        self.db_session.commit()
        return deleted_count > 0


def create_transcript_repository(db_session: Session) -> TranscriptRepoPort:
    """Factory function to create TranscriptRepository instance."""
    return TranscriptRepository(db_session)