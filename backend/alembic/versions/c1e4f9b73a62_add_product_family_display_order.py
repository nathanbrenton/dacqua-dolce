"""Add editable product family display order without altering catalog records.

Revision ID: c1e4f9b73a62
Revises: b32e10c7a9d4
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "c1e4f9b73a62"
down_revision: str | Sequence[str] | None = "b32e10c7a9d4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product_family_order",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("families_json", sa.Text(), nullable=False),
        sa.CheckConstraint("id = 1", name="product_family_order_singleton"),
        sa.CheckConstraint("revision > 0", name="product_family_order_revision_positive"),
    )
    op.execute(sa.text("""INSERT INTO product_family_order (id, revision, families_json)
        VALUES (1, 1, '["Refine", "Essence", "Origin", "Harmony"]')"""))


def downgrade() -> None:
    op.drop_table("product_family_order")
