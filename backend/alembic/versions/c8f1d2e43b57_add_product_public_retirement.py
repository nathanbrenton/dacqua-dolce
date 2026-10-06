"""Add scheduled public product retirement and replacement relationships.

Revision ID: c8f1d2e43b57
Revises: b7e0c9d31a42
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c8f1d2e43b57"
down_revision: str | None = "b7e0c9d31a42"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column(
            "public_retire_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "public_retirement_requires_discontinued",
        "products",
        "public_retire_at IS NULL OR lifecycle_status = 'discontinued'",
    )
    op.execute(
        "ALTER TYPE productrelationshiptype "
        "ADD VALUE IF NOT EXISTS 'replacement'"
    )


def downgrade() -> None:
    op.drop_constraint(
        "public_retirement_requires_discontinued",
        "products",
        type_="check",
    )
    op.drop_column("products", "public_retire_at")

    # PostgreSQL cannot directly drop an enum value. Rebuild the enum after
    # removing rows that use the PT48-only replacement relationship type.
    op.execute(
        "DELETE FROM product_relationships "
        "WHERE relationship_type::text = 'replacement'"
    )
    op.execute(
        "ALTER TABLE product_relationships "
        "ALTER COLUMN relationship_type TYPE VARCHAR "
        "USING relationship_type::text"
    )
    op.execute("DROP TYPE productrelationshiptype")
    op.execute(
        "CREATE TYPE productrelationshiptype AS ENUM ('option', 'accessory')"
    )
    op.execute(
        "ALTER TABLE product_relationships "
        "ALTER COLUMN relationship_type TYPE productrelationshiptype "
        "USING relationship_type::productrelationshiptype"
    )
