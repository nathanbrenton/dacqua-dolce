"""add recommendation context

Revision ID: a4d8c2e7f901
Revises: c41b7e2a9d63
Create Date: 2026-09-27

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a4d8c2e7f901"
down_revision: str | Sequence[str] | None = (
    "c41b7e2a9d63"
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "quote_requests",
        sa.Column(
            "recommendation_context",
            sa.JSON(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "quote_requests",
        "recommendation_context",
    )
