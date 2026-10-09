"""Update untouched product ordering seed without overwriting staff preferences.

Revision ID: d921ae0c7254
Revises: c1e4f9b73a62
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "d921ae0c7254"
down_revision: str | Sequence[str] | None = "c1e4f9b73a62"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Only modify the unedited original seed. A staff save increments revision.
    # Never change revision >= 2 or a nonmatching ordering value.
    op.execute(sa.text("""
        UPDATE product_family_order
        SET families_json = '["Refine", "Essence", "Harmony", "Origin"]'
        WHERE id = 1 AND revision = 1
          AND families_json = '["Refine", "Essence", "Origin", "Harmony"]'
    """))


def downgrade() -> None:
    # Intentionally leave mutable business preferences untouched.
    # Reverse migration must not overwrite order selected after the upgrade.
    pass
