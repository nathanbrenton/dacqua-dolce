"""add product architecture relationships

Revision ID: b7e3f1a92c40
Revises: a4d8c2e7f901
Create Date: 2026-09-27

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "b7e3f1a92c40"
down_revision: str | Sequence[str] | None = "a4d8c2e7f901"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("system_type", sa.String(length=160), nullable=True),
    )

    relationship_type = postgresql.ENUM(
        "option",
        "accessory",
        name="productrelationshiptype",
        create_type=False,
    )
    relationship_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "product_relationships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("related_product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relationship_type", relationship_type, nullable=False),
        sa.Column("public", sa.Boolean(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
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
            "product_id <> related_product_id", name="product_relationships_not_self"
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["related_product_id"], ["products.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "product_id",
            "related_product_id",
            "relationship_type",
            name="uq_product_relationships_pair_type",
        ),
    )
    op.create_index(
        "ix_product_relationships_product_id",
        "product_relationships",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        "ix_product_relationships_related_product_id",
        "product_relationships",
        ["related_product_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_product_relationships_related_product_id",
        table_name="product_relationships",
    )
    op.drop_index(
        "ix_product_relationships_product_id",
        table_name="product_relationships",
    )
    op.drop_table("product_relationships")
    op.drop_column("products", "system_type")
    postgresql.ENUM(name="productrelationshiptype").drop(
        op.get_bind(), checkfirst=True
    )
