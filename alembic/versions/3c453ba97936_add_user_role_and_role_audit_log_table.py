"""Add user role and role_audit_log table

Revision ID: 3c453ba97936
Revises: 5ba2c5fa0295
Create Date: 2025-08-15 16:16:43.688438

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c453ba97936'
down_revision: Union[str, Sequence[str], None] = '5ba2c5fa0295'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    from sqlalchemy.dialects import postgresql
    
    # Create role enum type
    role_enum = postgresql.ENUM('user', 'staff', 'admin', 'super_admin', name='userrole')
    role_enum.create(op.get_bind())
    
    # Add role column to user table with default value 'user'
    op.add_column('user', sa.Column('role', sa.Enum('user', 'staff', 'admin', 'super_admin', name='userrole'), 
                                     nullable=False, server_default='user'))
    
    # Add security-related columns to user table
    op.add_column('user', sa.Column('last_admin_login', sa.DateTime(timezone=True), nullable=True))
    op.add_column('user', sa.Column('admin_access_expires', sa.DateTime(timezone=True), nullable=True))
    op.add_column('user', sa.Column('allowed_ip_addresses', sa.JSON(), nullable=True))
    
    # Create index on role column for performance
    op.create_index('idx_user_role', 'user', ['role'])
    
    # Create role_audit_log table
    op.create_table('role_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('changed_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('old_role', sa.String(20), nullable=True),
        sa.Column('new_role', sa.String(20), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['changed_by_id'], ['user.id'], ),
    )
    
    # Create indexes on role_audit_log
    op.create_index('idx_role_audit_user', 'role_audit_log', ['user_id'])
    op.create_index('idx_role_audit_changed_by', 'role_audit_log', ['changed_by_id'])
    op.create_index('idx_role_audit_created_at', 'role_audit_log', ['created_at'])


def downgrade() -> None:
    """Downgrade schema."""
    from sqlalchemy.dialects import postgresql
    
    # Drop indexes on role_audit_log
    op.drop_index('idx_role_audit_created_at', table_name='role_audit_log')
    op.drop_index('idx_role_audit_changed_by', table_name='role_audit_log')
    op.drop_index('idx_role_audit_user', table_name='role_audit_log')
    
    # Drop role_audit_log table
    op.drop_table('role_audit_log')
    
    # Drop index on user role
    op.drop_index('idx_user_role', table_name='user')
    
    # Drop columns from user table
    op.drop_column('user', 'allowed_ip_addresses')
    op.drop_column('user', 'admin_access_expires')
    op.drop_column('user', 'last_admin_login')
    op.drop_column('user', 'role')
    
    # Drop role enum type
    role_enum = postgresql.ENUM('user', 'staff', 'admin', 'super_admin', name='userrole')
    role_enum.drop(op.get_bind())
