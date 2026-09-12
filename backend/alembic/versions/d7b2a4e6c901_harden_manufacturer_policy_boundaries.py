"""harden manufacturer policy boundaries

Revision ID: d7b2a4e6c901
Revises: 9a6c1b2d4e70
Create Date: 2026-09-12

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d7b2a4e6c901"
down_revision: str | Sequence[str] | None = (
    "9a6c1b2d4e70"
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column(
            "online_sale_approved",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.add_column(
        "product_documents",
        sa.Column(
            "public",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "product_documents",
        "public",
    )
    op.drop_column(
        "products",
        "online_sale_approved",
    )
