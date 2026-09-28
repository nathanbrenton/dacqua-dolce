"""add customer equipment ownership records

Revision ID: f7c3e1b8a420
Revises: e6b4c9a71f20
Create Date: 2026-09-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f7c3e1b8a420"
down_revision: str | Sequence[str] | None = "e6b4c9a71f20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customer_equipment",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("product_id", sa.UUID(), sa.ForeignKey("products.id", ondelete="SET NULL")),
        sa.Column(
            "variant_id",
            sa.UUID(),
            sa.ForeignKey("product_variants.id", ondelete="SET NULL"),
        ),
        sa.Column("sku_snapshot", sa.String(length=100), nullable=False),
        sa.Column("name_snapshot", sa.String(length=200), nullable=False),
        sa.Column("variant_snapshot", sa.String(length=160)),
        sa.Column("serial_number", sa.String(length=160)),
        sa.Column("location_label", sa.String(length=160)),
        sa.Column("installed_on", sa.Date()),
        sa.Column("last_service_on", sa.Date()),
        sa.Column("next_service_due_on", sa.Date()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_customer_equipment_user_id", "customer_equipment", ["user_id"])
    op.create_index("ix_customer_equipment_product_id", "customer_equipment", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_customer_equipment_product_id", table_name="customer_equipment")
    op.drop_index("ix_customer_equipment_user_id", table_name="customer_equipment")
    op.drop_table("customer_equipment")
