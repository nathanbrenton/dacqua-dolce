"""add inventory provenance

Revision ID: c4f7a2d91e85
Revises: b2e4f6a81c93
Create Date: 2026-09-29

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "c4f7a2d91e85"
down_revision: str | Sequence[str] | None = "b2e4f6a81c93"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    source_kind = postgresql.ENUM(
        "unspecified",
        "operator_entry",
        "supplier_report",
        "manufacturer_report",
        "internal_stock",
        name="inventory_source_kind",
    )
    source_kind.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "product_inventory",
        sa.Column(
            "source_kind",
            postgresql.ENUM(
                "unspecified",
                "operator_entry",
                "supplier_report",
                "manufacturer_report",
                "internal_stock",
                name="inventory_source_kind",
                create_type=False,
            ),
            nullable=False,
            server_default="unspecified",
        ),
    )
    op.add_column(
        "product_inventory",
        sa.Column("source_reference", sa.String(length=240), nullable=True),
    )
    op.add_column(
        "product_inventory",
        sa.Column("source_observed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column(
        "product_inventory",
        "source_kind",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("product_inventory", "source_observed_at")
    op.drop_column("product_inventory", "source_reference")
    op.drop_column("product_inventory", "source_kind")

    source_kind = postgresql.ENUM(
        "unspecified",
        "operator_entry",
        "supplier_report",
        "manufacturer_report",
        "internal_stock",
        name="inventory_source_kind",
    )
    source_kind.drop(op.get_bind(), checkfirst=True)
