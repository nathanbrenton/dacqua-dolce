"""Let operators mark a failed email delivery as reviewed.

Revision ID: e4b7c2d91f05
Revises: d921ae0c7254
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e4b7c2d91f05"
down_revision: str | Sequence[str] | None = "d921ae0c7254"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "email_deliveries",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "email_deliveries",
        sa.Column(
            "reviewed_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "users.id",
                name="fk_email_deliveries_reviewed_by_user_id_users",
                ondelete="SET NULL",
            ),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("email_deliveries", "reviewed_by_user_id")
    op.drop_column("email_deliveries", "reviewed_at")
