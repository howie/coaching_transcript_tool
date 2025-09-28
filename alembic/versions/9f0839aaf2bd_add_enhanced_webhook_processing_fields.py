"""add enhanced webhook processing fields

Revision ID: 9f0839aaf2bd
Revises: 35b2db1982ba
Create Date: 2025-08-28 21:57:27.427466

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9f0839aaf2bd"
down_revision: Union[str, Sequence[str], None] = "35b2db1982ba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add grace period and downgrade fields to saas_subscriptions
    op.add_column(
        "saas_subscriptions",
        sa.Column("grace_period_ends_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "saas_subscriptions",
        sa.Column("downgraded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "saas_subscriptions",
        sa.Column("downgrade_reason", sa.String(50), nullable=True),
    )

    # Add retry fields to subscription_payments
    op.add_column(
        "subscription_payments",
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "subscription_payments",
        sa.Column("max_retries", sa.Integer, nullable=True, default=3),
    )
    op.add_column(
        "subscription_payments",
        sa.Column("last_retry_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Add index for retry processing
    op.create_index(
        "ix_subscription_payments_retry_at", "subscription_payments", ["next_retry_at"]
    )

    # Add index for grace period processing
    op.create_index(
        "ix_saas_subscriptions_grace_period",
        "saas_subscriptions",
        ["grace_period_ends_at"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove indexes
    op.drop_index("ix_saas_subscriptions_grace_period", table_name="saas_subscriptions")
    op.drop_index(
        "ix_subscription_payments_retry_at", table_name="subscription_payments"
    )

    # Remove retry fields from subscription_payments
    op.drop_column("subscription_payments", "last_retry_at")
    op.drop_column("subscription_payments", "max_retries")
    op.drop_column("subscription_payments", "next_retry_at")

    # Remove grace period and downgrade fields from saas_subscriptions
    op.drop_column("saas_subscriptions", "downgrade_reason")
    op.drop_column("saas_subscriptions", "downgraded_at")
    op.drop_column("saas_subscriptions", "grace_period_ends_at")
