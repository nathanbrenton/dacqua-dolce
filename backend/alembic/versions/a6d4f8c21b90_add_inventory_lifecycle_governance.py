"""add inventory lifecycle governance

Revision ID: a6d4f8c21b90
Revises: e5a9d3c82b40
Create Date: 2026-10-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "a6d4f8c21b90"
down_revision: str | Sequence[str] | None = "e5a9d3c82b40"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    lifecycle_status = postgresql.ENUM(
        "active",
        "soon_discontinued",
        "discontinued",
        name="product_lifecycle_status",
    )
    lifecycle_status.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "products",
        sa.Column(
            "lifecycle_status",
            postgresql.ENUM(
                "active",
                "soon_discontinued",
                "discontinued",
                name="product_lifecycle_status",
                create_type=False,
            ),
            nullable=False,
            server_default="active",
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "allow_inquiry_when_unavailable",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "allow_formal_quote_when_unavailable",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "product_inventory",
        sa.Column("expected_available_on", sa.Date(), nullable=True),
    )

    op.alter_column("products", "lifecycle_status", server_default=None)
    op.alter_column(
        "products",
        "allow_inquiry_when_unavailable",
        server_default=None,
    )
    op.alter_column(
        "products",
        "allow_formal_quote_when_unavailable",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("product_inventory", "expected_available_on")
    op.drop_column("products", "allow_formal_quote_when_unavailable")
    op.drop_column("products", "allow_inquiry_when_unavailable")
    op.drop_column("products", "lifecycle_status")

    lifecycle_status = postgresql.ENUM(
        "active",
        "soon_discontinued",
        "discontinued",
        name="product_lifecycle_status",
    )
    lifecycle_status.drop(op.get_bind(), checkfirst=True)
