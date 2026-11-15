"""Store a customer's preferred contact method (email, call or text).

Revision ID: a6d3f1c8b259
Revises: e4b7c2d91f05
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a6d3f1c8b259"
down_revision: str | Sequence[str] | None = "e4b7c2d91f05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ALLOWED = "preferred_contact_method IN ('email', 'call', 'text')"


def upgrade() -> None:
    for table in ("quote_requests", "customer_profiles"):
        op.add_column(
            table,
            sa.Column("preferred_contact_method", sa.String(20), nullable=True),
        )
        op.create_check_constraint(
            "preferred_contact_method",
            table,
            ALLOWED,
        )


def downgrade() -> None:
    for table in ("customer_profiles", "quote_requests"):
        op.drop_constraint(
            "preferred_contact_method",
            table,
            type_="check",
        )
        op.drop_column(table, "preferred_contact_method")
