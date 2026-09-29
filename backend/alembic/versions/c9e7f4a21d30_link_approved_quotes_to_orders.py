"""link approved formal quotes to authoritative orders

Revision ID: c9e7f4a21d30
Revises: b4c8e2f91a60
Create Date: 2026-09-29

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c9e7f4a21d30"
down_revision: str | Sequence[str] | None = "b4c8e2f91a60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column(
            "formal_quote_id",
            sa.UUID(),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        op.f("fk_orders_formal_quote_id_formal_quotes"),
        "orders",
        "formal_quotes",
        ["formal_quote_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint(
        "uq_orders_formal_quote_id",
        "orders",
        ["formal_quote_id"],
    )

    # Formal quote item names allow 240 characters. Keep the downstream order
    # snapshot equally lossless when an approved quote becomes an order.
    op.alter_column(
        "order_items",
        "name_snapshot",
        existing_type=sa.String(length=200),
        type_=sa.String(length=240),
        existing_nullable=False,
    )

    # Provider checkout identifiers are the durable idempotency anchor for a
    # hosted checkout session. PostgreSQL permits multiple NULL values here,
    # so pre-provider historical rows remain compatible.
    op.create_unique_constraint(
        "uq_payment_provider_references_provider_checkout",
        "payment_provider_references",
        ["provider", "provider_checkout_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_payment_provider_references_provider_checkout",
        "payment_provider_references",
        type_="unique",
    )
    op.alter_column(
        "order_items",
        "name_snapshot",
        existing_type=sa.String(length=240),
        type_=sa.String(length=200),
        existing_nullable=False,
    )
    op.drop_constraint(
        "uq_orders_formal_quote_id",
        "orders",
        type_="unique",
    )
    op.drop_constraint(
        op.f("fk_orders_formal_quote_id_formal_quotes"),
        "orders",
        type_="foreignkey",
    )
    op.drop_column("orders", "formal_quote_id")
