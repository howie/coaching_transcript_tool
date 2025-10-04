"""increase_merchant_member_id_length_to_50

Revision ID: d291c8ef7fa0
Revises: 5572c099bcd1
Create Date: 2025-10-04 22:17:18.056546

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd291c8ef7fa0'
down_revision: Union[str, Sequence[str], None] = '5572c099bcd1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Increase merchant_member_id column length to accommodate MEMBER_<UUID> format.

    The merchant_member_id is generated as 'MEMBER_<uuid>' which is 45 characters,
    but the original column was VARCHAR(30). Increasing to VARCHAR(50) for safety.

    Affected tables:
    - ecpay_credit_authorizations.merchant_member_id
    - webhook_logs.merchant_member_id
    """
    # Increase column length in ecpay_credit_authorizations
    op.alter_column(
        'ecpay_credit_authorizations',
        'merchant_member_id',
        type_=sa.String(length=50),
        existing_type=sa.String(length=30),
        existing_nullable=False
    )

    # Increase column length in webhook_logs
    op.alter_column(
        'webhook_logs',
        'merchant_member_id',
        type_=sa.String(length=50),
        existing_type=sa.String(length=30),
        existing_nullable=True
    )


def downgrade() -> None:
    """Downgrade schema - restore original column length.

    WARNING: This may fail if any existing merchant_member_id values exceed 30 characters.
    """
    # Restore original column length in webhook_logs
    op.alter_column(
        'webhook_logs',
        'merchant_member_id',
        type_=sa.String(length=30),
        existing_type=sa.String(length=50),
        existing_nullable=True
    )

    # Restore original column length in ecpay_credit_authorizations
    op.alter_column(
        'ecpay_credit_authorizations',
        'merchant_member_id',
        type_=sa.String(length=30),
        existing_type=sa.String(length=50),
        existing_nullable=False
    )
