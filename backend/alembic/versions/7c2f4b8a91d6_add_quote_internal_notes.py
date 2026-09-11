"""add quote internal notes

Revision ID: 7c2f4b8a91d6
Revises: 35096160d6cf
Create Date: 2026-09-11

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7c2f4b8a91d6"
down_revision: str | Sequence[str] | None = "35096160d6cf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "quote_requests",
        sa.Column(
            "internal_notes",
            sa.Text(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column(
        "quote_requests",
        "internal_notes",
    )
