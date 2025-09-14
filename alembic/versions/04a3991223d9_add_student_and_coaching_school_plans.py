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
    
    # First, add lowercase versions of existing values
    op.execute("ALTER TYPE userplan ADD VALUE 'free'")
    op.execute("ALTER TYPE userplan ADD VALUE 'pro'")
    op.execute("ALTER TYPE userplan ADD VALUE 'enterprise'")
    
    # Then add new values
    op.execute("ALTER TYPE userplan ADD VALUE 'student'")
    op.execute("ALTER TYPE userplan ADD VALUE 'coaching_school'")
    
    # Migrate existing users to lowercase values
    op.execute("UPDATE \"user\" SET plan = 'free' WHERE plan = 'FREE'")
    op.execute("UPDATE \"user\" SET plan = 'pro' WHERE plan = 'PRO'")
    op.execute("UPDATE \"user\" SET plan = 'enterprise' WHERE plan = 'ENTERPRISE'")
    
    # Note: We keep both uppercase and lowercase for transition safety
    # The application will use lowercase values going forward


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
