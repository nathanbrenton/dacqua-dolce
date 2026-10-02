"""add warranty document provenance and snapshots

Revision ID: c3e7a1f49b20
Revises: b8d2f4c61a90
Create Date: 2026-10-02
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c3e7a1f49b20"
down_revision: str | Sequence[str] | None = "b8d2f4c61a90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "product_documents",
        sa.Column("source_reference", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "product_documents",
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "product_documents",
        sa.Column("verified_by_user_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_product_documents_verified_by_user_id_users"),
        "product_documents",
        "users",
        ["verified_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "formal_quote_warranty_snapshots",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("formal_quote_id", sa.UUID(), nullable=False),
        sa.Column("formal_quote_item_id", sa.UUID(), nullable=False),
        sa.Column("product_document_id", sa.UUID(), nullable=False),
        sa.Column("product_id_snapshot", sa.UUID(), nullable=False),
        sa.Column("sku_snapshot", sa.String(length=100), nullable=False),
        sa.Column("product_name_snapshot", sa.String(length=240), nullable=False),
        sa.Column("manufacturer_name_snapshot", sa.String(length=160), nullable=False),
        sa.Column("title_snapshot", sa.String(length=200), nullable=False),
        sa.Column("version_snapshot", sa.String(length=60), nullable=False),
        sa.Column("storage_path_snapshot", sa.String(length=500), nullable=False),
        sa.Column("content_type_snapshot", sa.String(length=120), nullable=False),
        sa.Column("checksum_sha256_snapshot", sa.String(length=64), nullable=False),
        sa.Column("source_reference_snapshot", sa.String(length=500), nullable=True),
        sa.Column("verified_at_snapshot", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["formal_quote_id"],
            ["formal_quotes.id"],
            name=op.f("fk_formal_quote_warranty_snapshots_formal_quote_id_formal_quotes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["formal_quote_item_id"],
            ["formal_quote_items.id"],
            name=op.f("fk_formal_quote_warranty_snapshots_formal_quote_item_id_formal_quote_items"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_document_id"],
            ["product_documents.id"],
            name=op.f("fk_formal_quote_warranty_snapshots_product_document_id_product_documents"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_formal_quote_warranty_snapshots")),
        sa.UniqueConstraint(
            "formal_quote_item_id",
            "product_document_id",
            name="uq_formal_quote_warranty_snapshots_item_document",
        ),
    )
    op.create_index(
        "ix_formal_quote_warranty_snapshots_quote_sort",
        "formal_quote_warranty_snapshots",
        ["formal_quote_id", "sort_order"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_formal_quote_warranty_snapshots_quote_sort",
        table_name="formal_quote_warranty_snapshots",
    )
    op.drop_table("formal_quote_warranty_snapshots")
    op.drop_constraint(
        op.f("fk_product_documents_verified_by_user_id_users"),
        "product_documents",
        type_="foreignkey",
    )
    op.drop_column("product_documents", "verified_by_user_id")
    op.drop_column("product_documents", "verified_at")
    op.drop_column("product_documents", "source_reference")
