"""fix_plan_configuration_enum_constraint

Revision ID: dc0e4ea7ee0a
Revises: 04a3991223d9
Create Date: 2025-09-11 07:34:44.826280

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "dc0e4ea7ee0a"
down_revision: Union[str, Sequence[str], None] = "04a3991223d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
