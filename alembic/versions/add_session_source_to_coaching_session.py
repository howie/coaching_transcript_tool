"""add_session_source_to_coaching_session

Revision ID: 5f8c9d3e2b1a
Revises: 4aa609eabb0b
Create Date: 2025-08-09 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5f8c9d3e2b1a"
down_revision: Union[str, Sequence[str], None] = "4aa609eabb0b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create SessionSource enum if it doesn't exist
    sessionsource_enum = postgresql.ENUM(
        "CLIENT", "FRIEND", "CLASSMATE", "SUBORDINATE", name="sessionsource"
    )
    sessionsource_enum.create(op.get_bind(), checkfirst=True)

    # Add source column to coaching_session table
    op.add_column(
        "coaching_session",
        sa.Column(
            "source", sessionsource_enum, nullable=False, server_default="CLIENT"
        ),
    )

    # Recreate indexes that were dropped in previous migrations
    op.create_index(
        op.f("idx_sessions_coach_date"),
        "coaching_session",
        ["coach_id", sa.desc("session_date")],
        unique=False,
    )
    op.create_index(
        op.f("idx_sessions_coach_currency_date"),
        "coaching_session",
        ["coach_id", "fee_currency", "session_date"],
        unique=False,
    )
    op.create_index(
        op.f("idx_clients_coach_name"), "client", ["coach_id", "name"], unique=False
    )
    # Skip the problematic unique index for now - will create it manually later
    # op.create_index('uq_clients_coach_email', 'client', ['coach_id', sa.func.lower('email')], unique=True, postgresql_where=sa.text('email IS NOT NULL AND email != \'\''))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    # op.drop_index('uq_clients_coach_email', table_name='client')  # Skipped in upgrade
    op.drop_index(op.f("idx_clients_coach_name"), table_name="client")
    op.drop_index(
        op.f("idx_sessions_coach_currency_date"), table_name="coaching_session"
    )
    op.drop_index(op.f("idx_sessions_coach_date"), table_name="coaching_session")

    # Drop source column from coaching_session table
    op.drop_column("coaching_session", "source")

    # Drop SessionSource enum
    sessionsource_enum = postgresql.ENUM(
        "CLIENT", "FRIEND", "CLASSMATE", "SUBORDINATE", name="sessionsource"
    )
    sessionsource_enum.drop(op.get_bind(), checkfirst=True)
