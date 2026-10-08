"""Persist inquiry origin while preserving legacy quote request history.

Revision ID: b32e10c7a9d4
Revises: a7d5e9c41b62
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b32e10c7a9d4"
down_revision: str | Sequence[str] | None = "a7d5e9c41b62"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    # All existing records remain explicitly legacy; no retroactive inference.
    op.add_column(
        "quote_requests",
        sa.Column(
            "inquiry_context",
            sa.String(length=40),
            nullable=False,
            server_default="legacy_quote_request",
        ),
    )

def downgrade() -> None:
    op.drop_column("quote_requests", "inquiry_context")
