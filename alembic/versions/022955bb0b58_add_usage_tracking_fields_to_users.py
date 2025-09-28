"""add_usage_tracking_fields_to_users

Revision ID: 022955bb0b58
Revises: 3c453ba97936
Create Date: 2025-08-15 22:45:05.173277

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "022955bb0b58"
down_revision: Union[str, Sequence[str], None] = "3c453ba97936"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add usage tracking fields to user table if they don't exist."""

    # Check if columns already exist before adding them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col["name"] for col in inspector.get_columns("user")]

    # Add session_count if it doesn't exist
    if "session_count" not in existing_columns:
        op.add_column(
            "user",
            sa.Column("session_count", sa.Integer(), nullable=True, server_default="0"),
        )

    # Add transcription_count if it doesn't exist
    if "transcription_count" not in existing_columns:
        op.add_column(
            "user",
            sa.Column(
                "transcription_count", sa.Integer(), nullable=True, server_default="0"
            ),
        )

    # Add usage_minutes if it doesn't exist
    if "usage_minutes" not in existing_columns:
        op.add_column(
            "user",
            sa.Column("usage_minutes", sa.Integer(), nullable=True, server_default="0"),
        )

    # Add last_usage_reset timestamp if it doesn't exist
    if "last_usage_reset" not in existing_columns:
        op.add_column(
            "user", sa.Column("last_usage_reset", sa.DateTime(), nullable=True)
        )

    # Create usage_history table for detailed tracking
    op.create_table(
        "usage_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "period_type", sa.String(20), nullable=False
        ),  # 'hourly', 'daily', 'monthly'
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sessions_created", sa.Integer(), server_default="0"),
        sa.Column("audio_minutes_processed", sa.Float(), server_default="0"),
        sa.Column("transcriptions_completed", sa.Integer(), server_default="0"),
        sa.Column("exports_generated", sa.Integer(), server_default="0"),
        sa.Column("storage_used_mb", sa.Float(), server_default="0"),
        sa.Column("unique_clients", sa.Integer(), server_default="0"),
        sa.Column("api_calls_made", sa.Integer(), server_default="0"),
        sa.Column("concurrent_sessions_peak", sa.Integer(), server_default="0"),
        sa.Column("plan_name", sa.String(20), nullable=True),
        sa.Column("plan_limits", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "user_id", "period_type", "period_start", name="unique_user_period"
        ),
    )

    # Create indexes for performance
    op.create_index(
        "idx_usage_history_user_period", "usage_history", ["user_id", "period_start"]
    )
    op.create_index("idx_usage_history_recorded", "usage_history", ["recorded_at"])

    # Create index on user table for usage queries
    op.create_index(
        "idx_user_usage_tracking",
        "user",
        ["session_count", "transcription_count", "usage_minutes"],
    )


def downgrade() -> None:
    """Remove usage tracking fields and tables."""

    # Drop indexes
    op.drop_index("idx_user_usage_tracking", table_name="user")
    op.drop_index("idx_usage_history_recorded", table_name="usage_history")
    op.drop_index("idx_usage_history_user_period", table_name="usage_history")

    # Drop usage_history table
    op.drop_table("usage_history")

    # Drop columns from user table
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col["name"] for col in inspector.get_columns("user")]

    if "last_usage_reset" in existing_columns:
        op.drop_column("user", "last_usage_reset")

    if "usage_minutes" in existing_columns:
        op.drop_column("user", "usage_minutes")

    if "transcription_count" in existing_columns:
        op.drop_column("user", "transcription_count")

    if "session_count" in existing_columns:
        op.drop_column("user", "session_count")
