"""add automated tax foundation

Revision ID: b7e0c9d31a42
Revises: a6d4f8c21b90
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b7e0c9d31a42"
down_revision: str | None = "a6d4f8c21b90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product_tax_classifications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "provider",
            sa.String(length=40),
            nullable=False,
        ),
        sa.Column(
            "tax_code",
            sa.String(length=80),
            nullable=False,
        ),
        sa.Column(
            "source_reference",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column(
            "verified_by_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "verified_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["verified_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "product_id",
            "provider",
            name="uq_product_tax_classifications_product_provider",
        ),
    )
    op.create_index(
        "ix_product_tax_classifications_provider_active",
        "product_tax_classifications",
        ["provider", "active"],
        unique=False,
    )

    op.create_table(
        "tax_calculations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "formal_quote_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "provider",
            sa.String(length=40),
            nullable=False,
        ),
        sa.Column(
            "provider_calculation_id",
            sa.String(length=300),
            nullable=False,
        ),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
        ),
        sa.Column(
            "line_items_amount_minor",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "shipping_amount_minor",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "tax_amount_minor",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "amount_total_minor",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "livemode",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "request_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "response_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "superseded_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "committed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "((formal_quote_id IS NOT NULL AND order_id IS NULL) OR "
            "(formal_quote_id IS NULL AND order_id IS NOT NULL))",
            name="tax_calculations_single_context",
        ),
        sa.CheckConstraint(
            "line_items_amount_minor >= 0",
            name="tax_calculations_line_items_nonnegative",
        ),
        sa.CheckConstraint(
            "shipping_amount_minor >= 0",
            name="tax_calculations_shipping_nonnegative",
        ),
        sa.CheckConstraint(
            "tax_amount_minor >= 0",
            name="tax_calculations_tax_nonnegative",
        ),
        sa.CheckConstraint(
            "amount_total_minor >= 0",
            name="tax_calculations_total_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["formal_quote_id"],
            ["formal_quotes.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider",
            "provider_calculation_id",
            name="uq_tax_calculations_provider_calculation",
        ),
    )
    op.create_index(
        "ix_tax_calculations_formal_quote_created",
        "tax_calculations",
        ["formal_quote_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_tax_calculations_order_created",
        "tax_calculations",
        ["order_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "tax_transactions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "calculation_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "provider",
            sa.String(length=40),
            nullable=False,
        ),
        sa.Column(
            "provider_transaction_id",
            sa.String(length=300),
            nullable=False,
        ),
        sa.Column(
            "provider_reference",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
        ),
        sa.Column(
            "tax_amount_minor",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "amount_total_minor",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "livemode",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "response_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "tax_amount_minor >= 0",
            name="tax_transactions_tax_nonnegative",
        ),
        sa.CheckConstraint(
            "amount_total_minor >= 0",
            name="tax_transactions_total_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["calculation_id"],
            ["tax_calculations.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "calculation_id",
            name="uq_tax_transactions_calculation",
        ),
        sa.UniqueConstraint(
            "order_id",
            name="uq_tax_transactions_order",
        ),
        sa.UniqueConstraint(
            "provider",
            "provider_transaction_id",
            name="uq_tax_transactions_provider_transaction",
        ),
    )


def downgrade() -> None:
    op.drop_table("tax_transactions")
    op.drop_index(
        "ix_tax_calculations_order_created",
        table_name="tax_calculations",
    )
    op.drop_index(
        "ix_tax_calculations_formal_quote_created",
        table_name="tax_calculations",
    )
    op.drop_table("tax_calculations")
    op.drop_index(
        "ix_product_tax_classifications_provider_active",
        table_name="product_tax_classifications",
    )
    op.drop_table("product_tax_classifications")
