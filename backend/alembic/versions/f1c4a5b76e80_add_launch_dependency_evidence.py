"""Add launch dependency evidence registry.

Revision ID: f1c4a5b76e80
Revises: e0b3f4a65d79
Create Date: 2026-10-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "f1c4a5b76e80"
down_revision: str | None = "e0b3f4a65d79"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "launch_dependency_evidence",
        sa.Column(
            "dependency_key",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "tracking_status",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "source_reference",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "evidence_received_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "internal_notes",
            sa.Text(),
            nullable=True,
        ),
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
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "dependency_key IN ("
            "'tax', "
            "'payment_checkout', "
            "'legal_review', "
            "'shipping_insurance', "
            "'support_phone', "
            "'installer_program'"
            ")",
            name="launch_dependency_evidence_key_supported",
        ),
        sa.CheckConstraint(
            "tracking_status IN ("
            "'action_required', "
            "'in_progress', "
            "'evidence_received', "
            "'verified', "
            "'blocked'"
            ")",
            name="launch_dependency_evidence_status_supported",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name="fk_launch_dependency_evidence_created_by_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_user_id"],
            ["users.id"],
            name="fk_launch_dependency_evidence_updated_by_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "dependency_key",
            name="pk_launch_dependency_evidence",
        ),
    )
    op.create_index(
        "ix_launch_dependency_evidence_status_updated",
        "launch_dependency_evidence",
        ["tracking_status", "updated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_launch_dependency_evidence_status_updated",
        table_name="launch_dependency_evidence",
    )
    op.drop_table("launch_dependency_evidence")
