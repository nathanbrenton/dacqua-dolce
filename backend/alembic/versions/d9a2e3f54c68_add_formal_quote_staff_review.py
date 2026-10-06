"""Add formal quote staff review evidence.

Revision ID: d9a2e3f54c68
Revises: c8f1d2e43b57
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "d9a2e3f54c68"
down_revision: str | None = "c8f1d2e43b57"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "formal_quotes",
        sa.Column(
            "staff_review_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "formal_quotes",
        sa.Column(
            "staff_review_reasons",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
    )
    op.add_column(
        "formal_quotes",
        sa.Column(
            "staff_review_completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "formal_quotes",
        sa.Column(
            "staff_review_completed_by_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "formal_quotes_staff_review_completion_complete",
        "formal_quotes",
        (
            "(staff_review_completed_at IS NULL "
            "AND staff_review_completed_by_user_id IS NULL) OR "
            "(staff_review_completed_at IS NOT NULL "
            "AND staff_review_completed_by_user_id IS NOT NULL)"
        ),
    )
    op.create_check_constraint(
        "formal_quotes_staff_review_completion_requires_review",
        "formal_quotes",
        "staff_review_completed_at IS NULL OR staff_review_required",
    )

    op.alter_column(
        "formal_quotes",
        "staff_review_required",
        server_default=None,
    )
    op.alter_column(
        "formal_quotes",
        "staff_review_reasons",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_constraint(
        "formal_quotes_staff_review_completion_requires_review",
        "formal_quotes",
        type_="check",
    )
    op.drop_constraint(
        "formal_quotes_staff_review_completion_complete",
        "formal_quotes",
        type_="check",
    )
    op.drop_column("formal_quotes", "staff_review_completed_by_user_id")
    op.drop_column("formal_quotes", "staff_review_completed_at")
    op.drop_column("formal_quotes", "staff_review_reasons")
    op.drop_column("formal_quotes", "staff_review_required")
