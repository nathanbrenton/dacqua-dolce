"""Add internal installer candidate registry.

Revision ID: e0b3f4a65d79
Revises: d9a2e3f54c68
Create Date: 2026-10-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e0b3f4a65d79"
down_revision: str | None = "d9a2e3f54c68"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "installer_candidates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("business_name", sa.String(length=160), nullable=False),
        sa.Column("contact_name", sa.String(length=160), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("phone", sa.String(length=80), nullable=True),
        sa.Column("website", sa.String(length=2048), nullable=True),
        sa.Column("service_area_notes", sa.Text(), nullable=True),
        sa.Column("source_reference", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="researching",
        ),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "updated_by_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "status IN ('researching', 'contacted', 'review_pending', 'inactive')",
            name="installer_candidates_status_supported",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_installer_candidates_status_updated",
        "installer_candidates",
        ["status", "updated_at"],
        unique=False,
    )
    op.alter_column(
        "installer_candidates",
        "status",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_installer_candidates_status_updated",
        table_name="installer_candidates",
    )
    op.drop_table("installer_candidates")
