"""refactor database column names for clarity and consistency

Revision ID: 0643b3b3d7b7
Revises: 2961da1deaa6
Create Date: 2025-08-13 06:53:57.660854

This migration refactors database column names for better clarity and consistency:

1. coaching_session table:
   - coach_id -> user_id (clearer that it references the user who owns the session)
   - audio_timeseq_id -> transcription_session_id (clearer reference to session.id)
   - transcript_timeseq_id -> REMOVED (unused field)

2. client table:
   - coach_id -> user_id (consistent with coaching_session)
   - client_status -> status (simpler, unambiguous in context)

3. session table:
   - duration_sec -> duration_seconds (more explicit unit naming)

4. transcript_segment table:
   - start_sec -> start_seconds (consistent unit naming)
   - end_sec -> end_seconds (consistent unit naming)

5. processing_status table:
   - No changes needed (already well-named)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0643b3b3d7b7"
down_revision: Union[str, Sequence[str], None] = "2961da1deaa6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply column renames for better clarity and consistency."""

    # 1. Rename columns in coaching_session table
    op.alter_column("coaching_session", "coach_id", new_column_name="user_id")
    op.alter_column(
        "coaching_session",
        "audio_timeseq_id",
        new_column_name="transcription_session_id",
    )

    # Drop the unused transcript_timeseq_id column
    op.drop_column("coaching_session", "transcript_timeseq_id")

    # 2. Rename columns in client table
    op.alter_column("client", "coach_id", new_column_name="user_id")
    op.alter_column("client", "client_status", new_column_name="status")

    # 3. Rename columns in session table
    op.alter_column("session", "duration_sec", new_column_name="duration_seconds")

    # 4. Rename columns in transcript_segment table
    op.alter_column("transcript_segment", "start_sec", new_column_name="start_seconds")
    op.alter_column("transcript_segment", "end_sec", new_column_name="end_seconds")

    # Update any indexes that might have been created with old column names
    # Note: PostgreSQL automatically updates foreign key constraints when columns are renamed  # noqa: E501

    # Drop old indexes (if they exist) and create new ones with better names
    try:
        op.drop_index("ix_coaching_session_coach_id", table_name="coaching_session")
    except:
        pass  # Index might not exist

    try:
        op.drop_index("ix_client_coach_id", table_name="client")
    except:
        pass  # Index might not exist

    # Create new indexes with updated column names
    op.create_index("ix_coaching_session_user_id", "coaching_session", ["user_id"])
    op.create_index("ix_client_user_id", "client", ["user_id"])


def downgrade() -> None:
    """Revert column renames to original names."""

    # Drop new indexes
    op.drop_index("ix_coaching_session_user_id", table_name="coaching_session")
    op.drop_index("ix_client_user_id", table_name="client")

    # 4. Revert transcript_segment column names
    op.alter_column("transcript_segment", "end_seconds", new_column_name="end_sec")
    op.alter_column("transcript_segment", "start_seconds", new_column_name="start_sec")

    # 3. Revert session column names
    op.alter_column("session", "duration_seconds", new_column_name="duration_sec")

    # 2. Revert client column names
    op.alter_column("client", "status", new_column_name="client_status")
    op.alter_column("client", "user_id", new_column_name="coach_id")

    # 1. Revert coaching_session column names
    # Re-add the dropped column
    op.add_column(
        "coaching_session",
        sa.Column(
            "transcript_timeseq_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
    )

    op.alter_column(
        "coaching_session",
        "transcription_session_id",
        new_column_name="audio_timeseq_id",
    )
    op.alter_column("coaching_session", "user_id", new_column_name="coach_id")

    # Recreate old indexes
    op.create_index("ix_coaching_session_coach_id", "coaching_session", ["coach_id"])
    op.create_index("ix_client_coach_id", "client", ["coach_id"])
