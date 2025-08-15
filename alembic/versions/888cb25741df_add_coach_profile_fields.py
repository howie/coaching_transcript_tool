"""add_coach_profile_fields

Revision ID: 888cb25741df
Revises: 6fedb09a97cd
Create Date: 2025-08-06 22:49:01.573176

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '888cb25741df'
down_revision: Union[str, Sequence[str], None] = '6fedb09a97cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create coach_profiles table
    op.create_table(
        'coach_profile',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('profile_photo_url', sa.String(length=512), nullable=True),
        sa.Column('public_email', sa.String(length=255), nullable=True),
        sa.Column('phone_country_code', sa.String(length=10), nullable=True),
        sa.Column('phone_number', sa.String(length=50), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('coaching_languages', sa.Text(), nullable=True),
        sa.Column('communication_tools', sa.Text(), nullable=True),
        sa.Column('line_id', sa.String(length=100), nullable=True),
        sa.Column('coach_experience', sa.String(length=50), nullable=True),
        sa.Column('training_institution', sa.String(length=255), nullable=True),
        sa.Column('certifications', sa.Text(), nullable=True),
        sa.Column('linkedin_url', sa.String(length=512), nullable=True),
        sa.Column('personal_website', sa.String(length=512), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('specialties', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_coach_profile_id'), 'coach_profile', ['id'], unique=False)
    
    # Create coaching_plans table
    op.create_table(
        'coaching_plan',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('coach_profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plan_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('number_of_sessions', sa.Integer(), nullable=True, default=1),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=True, default='NTD'),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('max_participants', sa.Integer(), nullable=True, default=1),
        sa.Column('booking_notice_hours', sa.Integer(), nullable=True, default=24),
        sa.Column('cancellation_notice_hours', sa.Integer(), nullable=True, default=24),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['coach_profile_id'], ['coach_profile.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_coaching_plan_id'), 'coaching_plan', ['id'], unique=False)
    
    # Create association tables for many-to-many relationships (optional, currently using JSON)
    op.create_table(
        'coach_languages',
        sa.Column('coach_profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('language', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['coach_profile_id'], ['coach_profile.id'], ),
        sa.PrimaryKeyConstraint('coach_profile_id', 'language')
    )
    
    op.create_table(
        'coach_communication_tools',
        sa.Column('coach_profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tool', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['coach_profile_id'], ['coach_profile.id'], ),
        sa.PrimaryKeyConstraint('coach_profile_id', 'tool')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop association tables
    op.drop_table('coach_communication_tools')
    op.drop_table('coach_languages')
    
    # Drop main tables
    op.drop_index(op.f('ix_coaching_plan_id'), table_name='coaching_plan')
    op.drop_table('coaching_plan')
    
    op.drop_index(op.f('ix_coach_profile_id'), table_name='coach_profile')
    op.drop_table('coach_profile')
