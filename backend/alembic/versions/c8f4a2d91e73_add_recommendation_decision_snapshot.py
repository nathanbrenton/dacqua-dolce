"""add recommendation decision snapshot

Revision ID: c8f4a2d91e73
Revises: b7e3f1a92c40
Create Date: 2026-09-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c8f4a2d91e73"
down_revision: str | Sequence[str] | None = "b7e3f1a92c40"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "quote_requests",
        sa.Column("recommendation_decision", sa.JSON(), nullable=True),
    )
    op.add_column(
        "quote_requests",
        sa.Column(
            "recommendation_policy_version",
            sa.String(length=40),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("quote_requests", "recommendation_policy_version")
    op.drop_column("quote_requests", "recommendation_decision")
