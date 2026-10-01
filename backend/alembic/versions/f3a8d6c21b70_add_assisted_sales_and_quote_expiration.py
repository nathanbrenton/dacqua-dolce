"""add assisted sales and quote expiration

Revision ID: f3a8d6c21b70
Revises: e2b7c4d91a60
Create Date: 2026-10-01

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f3a8d6c21b70"
down_revision: str | Sequence[str] | None = "e2b7c4d91a60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Fail closed for existing rows. Canonical catalog reconciliation then
    # marks non-whole-house products that do not require assisted review.
    op.add_column(
        "products",
        sa.Column(
            "assisted_sale_required",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
    )
    op.alter_column(
        "products",
        "assisted_sale_required",
        server_default=None,
    )

    # Existing presented/approved quotes are intentionally grandfathered with
    # NULL expiration. New presentations receive an explicit 30-day deadline.
    op.add_column(
        "formal_quotes",
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("formal_quotes", "expires_at")
    op.drop_column("products", "assisted_sale_required")
