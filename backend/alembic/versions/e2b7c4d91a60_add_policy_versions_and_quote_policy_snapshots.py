"""add policy versions and quote policy snapshots

Revision ID: e2b7c4d91a60
Revises: d6a4c8f21e93
Create Date: 2026-09-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e2b7c4d91a60"
down_revision: str | None = "d6a4c8f21e93"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

POLICY_KINDS = (
    "privacy",
    "terms",
    "shipping",
    "cancellation",
    "refund",
    "warranty",
    "installation",
)
POLICY_STATUSES = ("draft", "approved", "retired")


def upgrade() -> None:
    policy_kind = postgresql.ENUM(*POLICY_KINDS, name="policy_kind", create_type=False)
    policy_status = postgresql.ENUM(
        *POLICY_STATUSES,
        name="policy_document_status",
        create_type=False,
    )
    policy_kind.create(op.get_bind(), checkfirst=True)
    policy_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "policy_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", policy_kind, nullable=False),
        sa.Column("version", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", policy_status, nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
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
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("kind", "version", name="uq_policy_documents_kind_version"),
    )
    op.create_index(
        "uq_policy_documents_one_approved_per_kind",
        "policy_documents",
        ["kind"],
        unique=True,
        postgresql_where=sa.text("status = 'approved'"),
    )

    op.create_table(
        "formal_quote_policy_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("formal_quote_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("policy_document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", policy_kind, nullable=False),
        sa.Column("version_snapshot", sa.String(length=80), nullable=False),
        sa.Column("title_snapshot", sa.String(length=200), nullable=False),
        sa.Column("body_snapshot", sa.Text(), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("effective_at_snapshot", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["formal_quote_id"], ["formal_quotes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["policy_document_id"],
            ["policy_documents.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "formal_quote_id",
            "kind",
            name="uq_formal_quote_policy_snapshots_quote_kind",
        ),
    )


def downgrade() -> None:
    op.drop_table("formal_quote_policy_snapshots")
    op.drop_index(
        "uq_policy_documents_one_approved_per_kind",
        table_name="policy_documents",
    )
    op.drop_table("policy_documents")

    postgresql.ENUM(name="policy_document_status").drop(
        op.get_bind(),
        checkfirst=True,
    )
    postgresql.ENUM(name="policy_kind").drop(
        op.get_bind(),
        checkfirst=True,
    )
