"""add fulfillment tracking

Revision ID: f1c6a8d42e50
Revises: e7d4c2a91b60
Create Date: 2026-09-29

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "f1c6a8d42e50"
down_revision: str | Sequence[str] | None = "e7d4c2a91b60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    fulfillment_status = postgresql.ENUM(
        "not_started",
        "supplier_ordered",
        "received_ready",
        "shipped",
        "delivered",
        name="fulfillment_status",
    )
    fulfillment_status.create(
        op.get_bind(),
        checkfirst=True,
    )

    op.add_column(
        "orders",
        sa.Column(
            "fulfillment_status",
            fulfillment_status,
            server_default="not_started",
            nullable=False,
        ),
    )
    op.alter_column(
        "orders",
        "fulfillment_status",
        server_default=None,
    )
    op.add_column(
        "orders",
        sa.Column(
            "supplier_order_reference",
            sa.String(length=160),
            nullable=True,
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "supplier_ordered_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "received_ready_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "shipped_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "delivered_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "fulfillment_updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "order_items",
        sa.Column(
            "estimated_lead_time_snapshot",
            sa.String(length=120),
            nullable=True,
        ),
    )

    op.create_table(
        "order_shipments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("carrier", sa.String(length=100), nullable=False),
        sa.Column("tracking_number", sa.String(length=200), nullable=False),
        sa.Column("tracking_url", sa.String(length=2048), nullable=True),
        sa.Column("created_by_user_id", sa.UUID(), nullable=False),
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
            ["created_by_user_id"],
            ["users.id"],
            name=op.f(
                "fk_order_shipments_created_by_user_id_users"
            ),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name=op.f("fk_order_shipments_order_id_orders"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_order_shipments"),
        ),
        sa.UniqueConstraint(
            "order_id",
            name="uq_order_shipments_order_id",
        ),
    )


def downgrade() -> None:
    op.drop_table("order_shipments")

    op.drop_column(
        "order_items",
        "estimated_lead_time_snapshot",
    )

    op.drop_column("orders", "fulfillment_updated_at")
    op.drop_column("orders", "delivered_at")
    op.drop_column("orders", "shipped_at")
    op.drop_column("orders", "received_ready_at")
    op.drop_column("orders", "supplier_ordered_at")
    op.drop_column("orders", "supplier_order_reference")
    op.drop_column("orders", "fulfillment_status")

    postgresql.ENUM(
        name="fulfillment_status",
    ).drop(
        op.get_bind(),
        checkfirst=True,
    )
