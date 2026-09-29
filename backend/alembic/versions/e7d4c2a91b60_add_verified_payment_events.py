"""add verified payment provider events

Revision ID: e7d4c2a91b60
Revises: c9e7f4a21d30
Create Date: 2026-09-29

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e7d4c2a91b60"
down_revision: str | Sequence[str] | None = "c9e7f4a21d30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    payment_reference_status = postgresql.ENUM(
        "created",
        "pending",
        "succeeded",
        "failed",
        "cancelled",
        "refunded",
        name="payment_reference_status",
        create_type=False,
    )

    op.create_table(
        "payment_provider_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("payment_reference_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("provider_event_id", sa.String(length=300), nullable=False),
        sa.Column("status", payment_reference_status, nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("provider_payment_id", sa.String(length=300), nullable=True),
        sa.Column("provider_customer_id", sa.String(length=300), nullable=True),
        sa.Column("payment_method_type", sa.String(length=80), nullable=True),
        sa.Column("payment_method_brand", sa.String(length=80), nullable=True),
        sa.Column("payment_method_last4", sa.String(length=4), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "amount_minor IS NULL OR amount_minor >= 0",
            name=op.f("ck_payment_provider_events_amount_minor_nonnegative"),
        ),
        sa.ForeignKeyConstraint(
            ["payment_reference_id"],
            ["payment_provider_references.id"],
            name=op.f(
                "fk_payment_provider_events_payment_reference_id_"
                "payment_provider_references"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_payment_provider_events"),
        ),
        sa.UniqueConstraint(
            "provider",
            "provider_event_id",
            name="uq_payment_provider_events_provider_event",
        ),
    )
    op.create_index(
        "ix_payment_provider_events_reference_created",
        "payment_provider_events",
        ["payment_reference_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_payment_provider_events_reference_created",
        table_name="payment_provider_events",
    )
    op.drop_table("payment_provider_events")
