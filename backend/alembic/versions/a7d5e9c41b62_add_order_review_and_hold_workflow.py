"""Add order review checklist and hold workflow.

Revision ID: a7d5e9c41b62
Revises: f1c4a5b76e80
Create Date: 2026-10-07
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a7d5e9c41b62"
down_revision: str | None = "f1c4a5b76e80"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column(
            "review_customer_contact_reviewed",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "review_supplier_availability_verified",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "review_whole_order_reviewed",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "review_customer_contact_required",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "review_customer_contact_completed",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column(
        "orders",
        sa.Column("reviewed_by_user_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "orders",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "orders",
        sa.Column(
            "review_on_hold",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column(
        "orders",
        sa.Column("review_hold_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "orders",
        sa.Column("review_proposed_alternative", sa.Text(), nullable=True),
    )
    op.add_column(
        "orders",
        sa.Column("review_hold_started_by_user_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "orders",
        sa.Column("review_hold_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "orders",
        sa.Column("review_hold_released_by_user_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "orders",
        sa.Column("review_hold_released_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "orders",
        sa.Column("review_customer_response_note", sa.Text(), nullable=True),
    )
    op.create_foreign_key(
        "fk_orders_reviewed_by_user_id_users",
        "orders",
        "users",
        ["reviewed_by_user_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_orders_review_hold_started_by_user_id_users",
        "orders",
        "users",
        ["review_hold_started_by_user_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_orders_review_hold_released_by_user_id_users",
        "orders",
        "users",
        ["review_hold_released_by_user_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_orders_review_hold_released_by_user_id_users",
        "orders",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_orders_review_hold_started_by_user_id_users",
        "orders",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_orders_reviewed_by_user_id_users",
        "orders",
        type_="foreignkey",
    )
    for column in (
        "review_customer_response_note",
        "review_hold_released_at",
        "review_hold_released_by_user_id",
        "review_hold_started_at",
        "review_hold_started_by_user_id",
        "review_proposed_alternative",
        "review_hold_reason",
        "review_on_hold",
        "reviewed_at",
        "reviewed_by_user_id",
        "review_customer_contact_completed",
        "review_customer_contact_required",
        "review_whole_order_reviewed",
        "review_supplier_availability_verified",
        "review_customer_contact_reviewed",
    ):
        op.drop_column("orders", column)
