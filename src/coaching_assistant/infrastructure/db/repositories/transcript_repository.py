"""Transcript repository implementation using SQLAlchemy with Clean Architecture."""

from typing import List, Dict
from uuid import UUID
from sqlalchemy.orm import Session

from ....core.repositories.ports import TranscriptRepoPort
from ....core.models.transcript import TranscriptSegment
from ..models.transcript_model import TranscriptSegmentModel


class TranscriptRepository(TranscriptRepoPort):
    """SQLAlchemy implementation of TranscriptRepoPort using infrastructure models."""

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_by_session_id(self, session_id: UUID) -> List[TranscriptSegment]:
        """Get all transcript segments for a session."""
        orm_segments = (
            self.db_session.query(TranscriptSegmentModel)
            .filter(TranscriptSegmentModel.session_id == session_id)
            .order_by(TranscriptSegmentModel.start_seconds)
            .all()
        )
        return [segment.to_domain() for segment in orm_segments]

    def save_segments(self, segments: List[TranscriptSegment]) -> List[TranscriptSegment]:
        """Save multiple transcript segments."""
        orm_segments = []
        for segment in segments:
            orm_segment = TranscriptSegmentModel.from_domain(segment)
            self.db_session.add(orm_segment)
            orm_segments.append(orm_segment)

        self.db_session.flush()

        # Refresh all ORM segments
        for orm_segment in orm_segments:
            self.db_session.refresh(orm_segment)

        return [orm_segment.to_domain() for orm_segment in orm_segments]

    def update_speaker_roles(
        self, session_id: UUID, role_mappings: Dict[str, str]
    ) -> List[TranscriptSegment]:
        """Update speaker roles for session segments via SegmentRole table."""
        # Get all segments for the session
        orm_segments = (
            self.db_session.query(TranscriptSegmentModel)
            .filter(TranscriptSegmentModel.session_id == session_id)
            .all()
        )

        # TODO: Implement speaker role updates via SegmentRoleModel table
        # For now, return segments with UNKNOWN role (temporary fix)
        # This method should create/update entries in the segment_role table
        # to properly handle speaker role assignments

        return [orm_segment.to_domain() for orm_segment in orm_segments]

    def delete_by_session_id(self, session_id: UUID) -> bool:
        """Delete all segments for a session."""
        deleted_count = (
            self.db_session.query(TranscriptSegmentModel)
            .filter(TranscriptSegmentModel.session_id == session_id)
            .delete()
        )

        self.db_session.flush()
        return deleted_count > 0


def create_transcript_repository(db_session: Session) -> TranscriptRepoPort:
    """Factory function to create TranscriptRepository instance."""
    return TranscriptRepository(db_session)