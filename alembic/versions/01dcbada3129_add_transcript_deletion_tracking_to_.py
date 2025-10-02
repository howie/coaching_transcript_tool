"""add transcript deletion tracking to coaching sessions

Revision ID: 01dcbada3129
Revises: 900f713316c0
Create Date: 2025-10-02 17:59:34.018339

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "01dcbada3129"
down_revision: Union[str, Sequence[str], None] = "900f713316c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add transcript_deleted_at column to coaching_sessions
    op.add_column(
        "coaching_sessions",
        sa.Column("transcript_deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    # Add saved_speaking_stats column to coaching_sessions
    op.add_column(
        "coaching_sessions", sa.Column("saved_speaking_stats", sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove columns in reverse order
    op.drop_column("coaching_sessions", "saved_speaking_stats")
    op.drop_column("coaching_sessions", "transcript_deleted_at")
