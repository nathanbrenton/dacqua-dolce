"""add expiring cart inventory reservations

Revision ID: 9a6c1b2d4e70
Revises: 7c2f4b8a91d6
Create Date: 2026-09-12

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "9a6c1b2d4e70"
down_revision: str | Sequence[str] | None = (
    "7c2f4b8a91d6"
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "cart_items",
        sa.Column(
            "reservation_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_cart_items_reservation_scope",
        "cart_items",
        [
            "product_id",
            "variant_id",
            "reservation_expires_at",
        ],
        unique=False,
    )

    op.drop_constraint(
        op.f("ck_product_inventory_reserved_not_above_on_hand"),
        "product_inventory",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_product_inventory_quantity_reserved_nonnegative"),
        "product_inventory",
        type_="check",
    )

    op.drop_column(
        "product_inventory",
        "quantity_reserved",
    )


def downgrade() -> None:
    op.add_column(
        "product_inventory",
        sa.Column(
            "quantity_reserved",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )

    op.create_check_constraint(
        op.f("ck_product_inventory_quantity_reserved_nonnegative"),
        "product_inventory",
        "quantity_reserved >= 0",
    )
    op.create_check_constraint(
        op.f("ck_product_inventory_reserved_not_above_on_hand"),
        "product_inventory",
        "quantity_reserved <= quantity_on_hand",
    )

    op.drop_index(
        "ix_cart_items_reservation_scope",
        table_name="cart_items",
    )
    op.drop_column(
        "cart_items",
        "reservation_expires_at",
    )
