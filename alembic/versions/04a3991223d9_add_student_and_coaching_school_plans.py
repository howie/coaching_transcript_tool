"""add_student_and_coaching_school_plans

Revision ID: 04a3991223d9
Revises: 9f0839aaf2bd
Create Date: 2025-09-10 19:43:29.499540

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '04a3991223d9'
down_revision: Union[str, Sequence[str], None] = '9f0839aaf2bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add STUDENT and COACHING_SCHOOL plans to UserPlan enum."""

    # PRODUCTION SAFE: This migration has been manually applied to production
    # This code is now idempotent and safe to run multiple times

    connection = op.get_bind()

    # Check which enum values already exist to handle reruns safely
    existing_values_result = connection.execute(
        sa.text("""
            SELECT enumlabel
            FROM pg_enum
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userplan')
        """)
    )
    existing_values = {row[0] for row in existing_values_result}

    # Add new enum values only if they don't exist
    values_to_add = ['free', 'pro', 'enterprise', 'student', 'coaching_school']

    for value in values_to_add:
        if value not in existing_values:
            # Only add if it doesn't exist - safe for production reruns
            op.execute(f"ALTER TYPE userplan ADD VALUE '{value}'")

    # Only migrate data if there are users with uppercase values
    # This is safe because we check for existing data first
    migration_checks = [
        ("FREE", "free"),
        ("PRO", "pro"),
        ("ENTERPRISE", "enterprise")
    ]

    for old_value, new_value in migration_checks:
        # Check if there are any users with the old value
        check_result = connection.execute(
            sa.text(f"SELECT COUNT(*) FROM \"user\" WHERE plan = '{old_value}'")
        )
        count = check_result.scalar()

        if count > 0:
            # Only update if there are users to migrate
            op.execute(f"UPDATE \"user\" SET plan = '{new_value}' WHERE plan = '{old_value}'")

    # This migration is now safe for production and development environments


def downgrade() -> None:
    """Remove STUDENT and COACHING_SCHOOL plans from UserPlan enum."""
    
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type, which is complex
    # In practice, we keep deprecated values for data safety
    
    # Update any users on the new plans to pro as fallback
    op.execute("""
        UPDATE "user" 
        SET plan = 'pro' 
        WHERE plan IN ('student', 'coaching_school')
    """)
    
    # Migrate back to uppercase for safety
    op.execute("UPDATE \"user\" SET plan = 'FREE' WHERE plan = 'free'")
    op.execute("UPDATE \"user\" SET plan = 'PRO' WHERE plan = 'pro'")
    op.execute("UPDATE \"user\" SET plan = 'ENTERPRISE' WHERE plan = 'enterprise'")
    
    # Note: The enum values remain in the schema for safety
    # but are no longer used by the application
