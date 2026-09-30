"""add commercial quote and order snapshots

Revision ID: d6a4c8f21e93
Revises: c4f7a2d91e85
Create Date: 2026-09-29

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d6a4c8f21e93"
down_revision: str | Sequence[str] | None = "c4f7a2d91e85"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_CHARGE_KIND_CHECK = (
    "kind IN ('shipping', 'tax', 'installation', 'discount', "
    "'other_charge', 'other_credit')"
)
_CHARGE_SIGN_CHECK = (
    "((kind IN ('shipping', 'tax', 'installation', 'other_charge') "
    "AND amount_minor > 0) OR "
    "(kind IN ('discount', 'other_credit') AND amount_minor < 0))"
)


def upgrade() -> None:
    op.add_column(
        "formal_quotes",
        sa.Column(
            "charges_amount_minor",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "formal_quotes",
        sa.Column(
            "total_amount_minor",
            sa.BigInteger(),
            nullable=True,
        ),
    )
    op.add_column(
        "formal_quotes",
        sa.Column(
            "delivery_address_snapshot",
            sa.JSON(),
            nullable=True,
        ),
    )
    op.add_column(
        "formal_quotes",
        sa.Column(
            "billing_address_snapshot",
            sa.JSON(),
            nullable=True,
        ),
    )
    op.execute(
        "UPDATE formal_quotes "
        "SET total_amount_minor = subtotal_amount_minor "
        "WHERE total_amount_minor IS NULL"
    )
    op.alter_column(
        "formal_quotes",
        "total_amount_minor",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
    op.create_check_constraint(
        op.f("ck_formal_quotes_formal_quotes_total_nonnegative"),
        "formal_quotes",
        "total_amount_minor >= 0",
    )
    op.create_check_constraint(
        op.f("ck_formal_quotes_formal_quotes_total_matches_components"),
        "formal_quotes",
        "total_amount_minor = subtotal_amount_minor + charges_amount_minor",
    )

    op.create_table(
        "formal_quote_charges",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("formal_quote_id", sa.UUID(), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("label", sa.String(length=160), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            _CHARGE_KIND_CHECK,
            name=op.f("ck_formal_quote_charges_formal_quote_charges_kind_valid"),
        ),
        sa.CheckConstraint(
            _CHARGE_SIGN_CHECK,
            name=op.f("ck_formal_quote_charges_formal_quote_charges_amount_sign_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["formal_quote_id"],
            ["formal_quotes.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.add_column(
        "orders",
        sa.Column(
            "subtotal_amount_minor",
            sa.BigInteger(),
            nullable=True,
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "charges_amount_minor",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "delivery_address_snapshot",
            sa.JSON(),
            nullable=True,
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "billing_address_snapshot",
            sa.JSON(),
            nullable=True,
        ),
    )
    op.execute(
        "UPDATE orders "
        "SET subtotal_amount_minor = total_amount_minor "
        "WHERE subtotal_amount_minor IS NULL"
    )
    op.alter_column(
        "orders",
        "subtotal_amount_minor",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
    op.create_check_constraint(
        op.f("ck_orders_orders_subtotal_nonnegative"),
        "orders",
        "subtotal_amount_minor >= 0",
    )
    op.create_check_constraint(
        op.f("ck_orders_orders_total_matches_components"),
        "orders",
        "total_amount_minor = subtotal_amount_minor + charges_amount_minor",
    )

    op.create_table(
        "order_charges",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("label", sa.String(length=160), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            _CHARGE_KIND_CHECK,
            name=op.f("ck_order_charges_order_charges_kind_valid"),
        ),
        sa.CheckConstraint(
            _CHARGE_SIGN_CHECK,
            name=op.f("ck_order_charges_order_charges_amount_sign_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("order_charges")
    op.drop_constraint(
        op.f("ck_orders_orders_total_matches_components"),
        "orders",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_orders_orders_subtotal_nonnegative"),
        "orders",
        type_="check",
    )
    op.drop_column("orders", "billing_address_snapshot")
    op.drop_column("orders", "delivery_address_snapshot")
    op.drop_column("orders", "charges_amount_minor")
    op.drop_column("orders", "subtotal_amount_minor")

    op.drop_table("formal_quote_charges")
    op.drop_constraint(
        op.f("ck_formal_quotes_formal_quotes_total_matches_components"),
        "formal_quotes",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_formal_quotes_formal_quotes_total_nonnegative"),
        "formal_quotes",
        type_="check",
    )
    op.drop_column("formal_quotes", "billing_address_snapshot")
    op.drop_column("formal_quotes", "delivery_address_snapshot")
    op.drop_column("formal_quotes", "total_amount_minor")
    op.drop_column("formal_quotes", "charges_amount_minor")
