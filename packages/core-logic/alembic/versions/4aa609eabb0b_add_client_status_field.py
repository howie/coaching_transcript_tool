"""add_client_status_field

Revision ID: 4aa609eabb0b
Revises: e473fb418e6a
Create Date: 2025-08-07 16:12:10.731207

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4aa609eabb0b'
down_revision: Union[str, Sequence[str], None] = 'e473fb418e6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add client_status column to client table
    op.add_column('client', sa.Column('client_status', sa.String(50), nullable=False, server_default='first_session'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove client_status column from client table
    op.drop_column('client', 'client_status')
