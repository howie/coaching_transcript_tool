"""Add webhook logging and monitoring tables

Revision ID: 35b2db1982ba
Revises: 87f04209b63f
Create Date: 2025-08-20 19:50:13.321868

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "35b2db1982ba"
down_revision: Union[str, Sequence[str], None] = "87f04209b63f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create webhook_logs table
    op.create_table(
        "webhook_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Webhook details
        sa.Column("webhook_type", sa.String(50), nullable=False, index=True),
        sa.Column("source", sa.String(50), default="ecpay", nullable=False),
        # Request information
        sa.Column("method", sa.String(10), default="POST", nullable=False),
        sa.Column("endpoint", sa.String(255), nullable=False),
        sa.Column("headers", postgresql.JSON, nullable=True),
        sa.Column("raw_body", sa.Text, nullable=True),
        sa.Column("form_data", postgresql.JSON, nullable=True),
        # Processing information
        sa.Column(
            "status", sa.String(20), default="received", nullable=False, index=True
        ),
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_completed_at", sa.DateTime(timezone=True), nullable=True),
        # Result
        sa.Column("success", sa.Boolean, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("response_body", sa.Text, nullable=True),
        # Related entities
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "subscription_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("saas_subscriptions.id"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "payment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("subscription_payments.id"),
            nullable=True,
            index=True,
        ),
        # ECPay specific fields
        sa.Column("merchant_member_id", sa.String(30), nullable=True, index=True),
        sa.Column("gwsr", sa.String(30), nullable=True, index=True),
        sa.Column("rtn_code", sa.String(10), nullable=True),
        # Security verification
        sa.Column("check_mac_value_verified", sa.Boolean, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),  # Support IPv6
        # Retry information
        sa.Column("retry_count", sa.Integer, default=0, nullable=False),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # Create indexes for better query performance
    op.create_index("idx_webhook_logs_received_at", "webhook_logs", ["received_at"])
    op.create_index(
        "idx_webhook_logs_type_status", "webhook_logs", ["webhook_type", "status"]
    )
    op.create_index(
        "idx_webhook_logs_merchant_member", "webhook_logs", ["merchant_member_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index("idx_webhook_logs_merchant_member", "webhook_logs")
    op.drop_index("idx_webhook_logs_type_status", "webhook_logs")
    op.drop_index("idx_webhook_logs_received_at", "webhook_logs")

    # Drop table
    op.drop_table("webhook_logs")
