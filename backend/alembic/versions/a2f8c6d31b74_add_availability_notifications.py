"""add customer availability lead time and stock notification records

Revision ID: a2f8c6d31b74
Revises: f7c3e1b8a420
Create Date: 2026-09-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a2f8c6d31b74"
down_revision: str | Sequence[str] | None = "f7c3e1b8a420"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # PostgreSQL enum values can be extended safely in-place. Existing values
    # are preserved for historical product documents.
    op.execute("ALTER TYPE product_document_type ADD VALUE IF NOT EXISTS 'owners_manual'")
    op.execute("ALTER TYPE product_document_type ADD VALUE IF NOT EXISTS 'maintenance_guide'")
    op.execute("ALTER TYPE product_document_type ADD VALUE IF NOT EXISTS 'service_schedule'")
    op.execute("ALTER TYPE product_document_type ADD VALUE IF NOT EXISTS 'water_test_report'")

    op.add_column(
        "product_inventory",
        sa.Column("estimated_lead_time", sa.String(length=120)),
    )

    op.create_table(
        "stock_notification_subscriptions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "product_id",
            sa.UUID(),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notified_at", sa.DateTime(timezone=True)),
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
        sa.UniqueConstraint(
            "product_id",
            "email",
            name="uq_stock_notification_product_email",
        ),
    )
    op.create_index(
        "ix_stock_notification_subscriptions_product_id",
        "stock_notification_subscriptions",
        ["product_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_stock_notification_subscriptions_product_id",
        table_name="stock_notification_subscriptions",
    )
    op.drop_table("stock_notification_subscriptions")
    op.drop_column("product_inventory", "estimated_lead_time")
    # PostgreSQL enum values are intentionally retained on downgrade. Removing
    # enum labels is destructive and would require recreating the enum type.
