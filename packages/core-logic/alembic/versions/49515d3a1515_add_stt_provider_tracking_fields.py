"""add_stt_provider_tracking_fields

Revision ID: 49515d3a1515
Revises: 0643b3b3d7b7
Create Date: 2025-08-13 22:25:12.224533

Add STT provider tracking fields to session table for AssemblyAI integration:
- stt_provider: Track which STT provider was used ('google', 'assemblyai')
- provider_metadata: Store provider-specific metadata as JSONB

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '49515d3a1515'
down_revision: Union[str, Sequence[str], None] = '0643b3b3d7b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add stt_provider column to session table
    op.add_column('session', sa.Column(
        'stt_provider', 
        sa.String(50), 
        server_default='google', 
        nullable=False
    ))
    
    # Add provider_metadata column to session table
    op.add_column('session', sa.Column(
        'provider_metadata', 
        JSONB(), 
        server_default='{}', 
        nullable=False
    ))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the added columns
    op.drop_column('session', 'provider_metadata')
    op.drop_column('session', 'stt_provider')
