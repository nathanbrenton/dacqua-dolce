"""add formal quote revisions

Revision ID: b4c8e2f91a60
Revises: a2f8c6d31b74
Create Date: 2026-09-29

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "b4c8e2f91a60"
down_revision: str | Sequence[str] | None = "a2f8c6d31b74"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


formal_quote_status = postgresql.ENUM(
    "draft",
    "presented",
    "approved",
    "superseded",
    name="formal_quote_status",
    create_type=False,
)


def upgrade() -> None:
    formal_quote_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "formal_quotes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("quote_request_id", sa.UUID(), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            formal_quote_status,
            nullable=False,
        ),
        sa.Column("customer_user_id", sa.UUID(), nullable=True),
        sa.Column("authored_by_user_id", sa.UUID(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("subtotal_amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("customer_note", sa.Text(), nullable=True),
        sa.Column("presented_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by_user_id", sa.UUID(), nullable=True),
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
            "revision_number > 0",
            name=op.f("ck_formal_quotes_formal_quotes_revision_positive"),
        ),
        sa.CheckConstraint(
            "subtotal_amount_minor >= 0",
            name=op.f("ck_formal_quotes_formal_quotes_subtotal_nonnegative"),
        ),
        sa.ForeignKeyConstraint(
            ["approved_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["authored_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["customer_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["quote_request_id"],
            ["quote_requests.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "quote_request_id",
            "revision_number",
            name="uq_formal_quotes_request_revision",
        ),
    )

    op.create_table(
        "formal_quote_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("formal_quote_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=True),
        sa.Column("variant_id", sa.UUID(), nullable=True),
        sa.Column("sku_snapshot", sa.String(length=100), nullable=False),
        sa.Column("name_snapshot", sa.String(length=240), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("line_total_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column(
            "pricing_policy_mode_snapshot",
            sa.String(length=40),
            nullable=False,
        ),
        sa.Column(
            "estimated_lead_time_snapshot",
            sa.String(length=120),
            nullable=True,
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "line_total_minor >= 0",
            name=op.f("ck_formal_quote_items_formal_quote_items_line_total_nonnegative"),
        ),
        sa.CheckConstraint(
            "quantity > 0",
            name=op.f("ck_formal_quote_items_formal_quote_items_quantity_positive"),
        ),
        sa.CheckConstraint(
            "unit_amount_minor >= 0",
            name=op.f("ck_formal_quote_items_formal_quote_items_unit_amount_nonnegative"),
        ),
        sa.ForeignKeyConstraint(
            ["formal_quote_id"],
            ["formal_quotes.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["variant_id"],
            ["product_variants.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("formal_quote_items")
    op.drop_table("formal_quotes")
    formal_quote_status.drop(op.get_bind(), checkfirst=True)
