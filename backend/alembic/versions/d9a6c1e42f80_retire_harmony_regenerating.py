"""retire harmony regenerating

Revision ID: d9a6c1e42f80
Revises: c8f4a2d91e73
Create Date: 2026-09-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d9a6c1e42f80"
down_revision: str | Sequence[str] | None = "c8f4a2d91e73"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # The client explicitly removed this configuration from the product lineup.
    # Keep the row for historical references, but make it non-sellable/non-public.
    op.execute(
        sa.text(
            "UPDATE products "
            "SET active = false, online_sale_approved = false "
            "WHERE sku = 'DD15CAT-TTACRV'"
        )
    )


def downgrade() -> None:
    # Downgrade restores only the lifecycle flag changed by this migration.
    # Canonical catalog reconciliation still governs descriptive metadata.
    op.execute(
        sa.text(
            "UPDATE products "
            "SET active = true "
            "WHERE sku = 'DD15CAT-TTACRV'"
        )
    )
