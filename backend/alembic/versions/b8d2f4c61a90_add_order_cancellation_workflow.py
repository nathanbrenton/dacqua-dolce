"""add order cancellation workflow

Revision ID: b8d2f4c61a90
Revises: a5c9e2d41f70
Create Date: 2026-10-01
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b8d2f4c61a90"
down_revision: str | Sequence[str] | None = "a5c9e2d41f70"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "order_cancellation_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("requested_by_user_id", sa.UUID(), nullable=False),
        sa.Column("eligibility_mode", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "supplier_ordered_at_snapshot",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("reviewed_by_user_id", sa.UUID(), nullable=True),
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("completed_by_user_id", sa.UUID(), nullable=True),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
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
        sa.CheckConstraint(
            "eligibility_mode IN ('unrestricted', 'manual_review')",
            name=op.f(
                "ck_order_cancellation_requests_cancellation_mode_valid"
            ),
        ),
        sa.CheckConstraint(
            "status IN ('requested', 'approved', 'declined', 'completed')",
            name=op.f(
                "ck_order_cancellation_requests_cancellation_status_valid"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["completed_by_user_id"],
            ["users.id"],
            name=op.f(
                "fk_order_cancellation_requests_completed_by_user_id_users"
            ),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name=op.f(
                "fk_order_cancellation_requests_order_id_orders"
            ),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_user_id"],
            ["users.id"],
            name=op.f(
                "fk_order_cancellation_requests_requested_by_user_id_users"
            ),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"],
            ["users.id"],
            name=op.f(
                "fk_order_cancellation_requests_reviewed_by_user_id_users"
            ),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_order_cancellation_requests"),
        ),
        sa.UniqueConstraint(
            "order_id",
            name="uq_order_cancellation_requests_order_id",
        ),
    )
    op.create_index(
        "ix_order_cancellation_requests_status_created",
        "order_cancellation_requests",
        ["status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_order_cancellation_requests_status_created",
        table_name="order_cancellation_requests",
    )
    op.drop_table("order_cancellation_requests")
