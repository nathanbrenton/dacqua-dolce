"""add consumable replacement metadata

Revision ID: a8d5c3f19b72
Revises: f1c6a8d42e50
Create Date: 2026-09-29

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a8d5c3f19b72"
down_revision: str | Sequence[str] | None = "f1c6a8d42e50"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "product_relationships",
        sa.Column(
            "is_consumable",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.alter_column(
        "product_relationships",
        "is_consumable",
        server_default=None,
    )
    op.add_column(
        "product_relationships",
        sa.Column(
            "replacement_interval_days",
            sa.Integer(),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        op.f("ck_product_relationships_consumable_interval_valid"),
        "product_relationships",
        (
            "replacement_interval_days IS NULL OR "
            "(is_consumable AND replacement_interval_days > 0)"
        ),
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_product_relationships_consumable_interval_valid"),
        "product_relationships",
        type_="check",
    )
    op.drop_column(
        "product_relationships",
        "replacement_interval_days",
    )
    op.drop_column(
        "product_relationships",
        "is_consumable",
    )
