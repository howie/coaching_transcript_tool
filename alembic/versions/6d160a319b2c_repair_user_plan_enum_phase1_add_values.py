"""repair_user_plan_enum_phase1_add_values

PHASE 1: Add lowercase enum values with commit

This migration fixes the production issue caused by migration 900f713316c0
which violated PostgreSQL's enum transaction safety rules.

PostgreSQL Rule:
    New enum values MUST be committed before they can be used in DML statements.

Problem in 900f713316c0:
    1. Added new enum values (free, pro, enterprise)
    2. Immediately tried to UPDATE user records in same transaction
    3. PostgreSQL rejected: "unsafe use of new value"

Solution (Two-Phase Migration):
    Phase 1 (THIS MIGRATION): Add lowercase enum values + COMMIT
    Phase 2 (NEXT MIGRATION): Migrate user data from uppercase to lowercase

Reference:
    @docs/claude/enum-migration-best-practices.md
    @docs/issues/production-subscription-auth-enum-failure.md

Revision ID: 6d160a319b2c
Revises: 01dcbada3129
Create Date: 2025-10-04 20:24:26.842714

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '6d160a319b2c'
down_revision: Union[str, Sequence[str], None] = '01dcbada3129'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Phase 1: Add lowercase enum values with immediate commit.

    This ensures new values are available for use in Phase 2 migration.
    """
    connection = op.get_bind()

    # Get existing enum values
    existing_values_result = connection.execute(
        sa.text("""
            SELECT enumlabel
            FROM pg_enum
            WHERE enumtypid = (
                SELECT oid FROM pg_type WHERE typname = 'userplan'
            )
        """)
    )
    existing_values = {row[0] for row in existing_values_result}

    # Define required lowercase values
    # (uppercase values FREE, PRO, ENTERPRISE should already exist from old migrations)
    required_lowercase_values = ["free", "pro", "enterprise", "student", "coaching_school"]

    # Add missing lowercase enum values
    added_count = 0
    for value in required_lowercase_values:
        if value not in existing_values:
            op.execute(f"ALTER TYPE userplan ADD VALUE '{value}'")
            added_count += 1

    # CRITICAL: Commit immediately to make new enum values available
    # This is required by PostgreSQL before the values can be used in DML
    if added_count > 0:
        op.execute("COMMIT")

    # Note: Data migration happens in Phase 2 (next migration)


def downgrade() -> None:
    """
    Downgrade is not supported for enum value additions.

    PostgreSQL does not support removing enum values in a safe way.
    This is intentional - enum values should be additive only.
    """
    # Cannot safely remove enum values from PostgreSQL
    # This would require recreating the entire type
    pass
