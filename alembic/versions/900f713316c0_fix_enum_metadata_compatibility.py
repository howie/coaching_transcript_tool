"""fix_enum_metadata_compatibility

Revision ID: 900f713316c0
Revises: 04a3991223d9
Create Date: 2025-09-28 12:15:10.738605

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "900f713316c0"
down_revision: Union[str, Sequence[str], None] = "dc0e4ea7ee0a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix enum metadata compatibility for native_enum=False models."""

    # This migration ensures compatibility with native_enum=False
    # All enum operations have already been applied by previous migrations

    connection = op.get_bind()

    # Verify that all required enum values exist in the database
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

    required_values = [
        "FREE",
        "PRO",
        "ENTERPRISE",
        "free",
        "pro",
        "enterprise",
        "student",
        "coaching_school",
    ]

    # Add any missing enum values (defensive programming)
    for value in required_values:
        if value not in existing_values:
            op.execute(f"ALTER TYPE userplan ADD VALUE '{value}'")

    # Ensure all user data uses lowercase values for consistency
    # This is safe to run multiple times
    uppercase_to_lowercase = [
        ("FREE", "free"),
        ("PRO", "pro"),
        ("ENTERPRISE", "enterprise"),
    ]

    for old_value, new_value in uppercase_to_lowercase:
        # Check if there are users with uppercase values
        check_result = connection.execute(
            sa.text(f"SELECT COUNT(*) FROM \"user\" WHERE plan = '{old_value}'")
        )
        count = check_result.scalar()

        if count > 0:
            # Migrate remaining uppercase values to lowercase
            op.execute(
                f"UPDATE \"user\" SET plan = '{new_value}' WHERE plan = '{old_value}'"
            )

        # Also check other tables that use the enum
        table_columns = [
            ("plan_configurations", "plan_type"),
            ("subscription_history", "old_plan"),
            ("subscription_history", "new_plan"),
        ]
        for table, column in table_columns:
            try:
                check_result = connection.execute(
                    sa.text(
                        f'SELECT COUNT(*) FROM "{table}" '
                        f"WHERE {column} = '{old_value}'"
                    )
                )
                count = check_result.scalar()

                if count > 0:
                    op.execute(
                        f"UPDATE \"{table}\" SET {column} = '{new_value}' "
                        f"WHERE {column} = '{old_value}'"
                    )
            except Exception:
                # Table might not exist or column might be nullable
                pass


def downgrade() -> None:
    """Downgrade schema."""

    # For safety, we don't remove enum values in downgrade
    # This ensures data integrity is maintained

    # Optionally, we could migrate data back to uppercase
    # but this is not recommended as it could break applications
    pass
