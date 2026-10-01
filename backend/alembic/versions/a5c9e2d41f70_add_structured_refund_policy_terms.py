"""add structured refund policy terms

Revision ID: a5c9e2d41f70
Revises: f3a8d6c21b70
Create Date: 2026-10-01
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a5c9e2d41f70"
down_revision: str | None = "f3a8d6c21b70"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "policy_documents",
        sa.Column("structured_terms", sa.JSON(), nullable=True),
    )
    op.add_column(
        "formal_quote_policy_snapshots",
        sa.Column("structured_terms_snapshot", sa.JSON(), nullable=True),
    )
    op.add_column(
        "formal_quote_policy_snapshots",
        sa.Column("structured_terms_sha256", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column(
        "formal_quote_policy_snapshots",
        "structured_terms_sha256",
    )
    op.drop_column(
        "formal_quote_policy_snapshots",
        "structured_terms_snapshot",
    )
    op.drop_column(
        "policy_documents",
        "structured_terms",
    )
