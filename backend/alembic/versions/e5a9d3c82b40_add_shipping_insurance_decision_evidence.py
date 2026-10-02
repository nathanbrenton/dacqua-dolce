"""add shipping insurance decision evidence

Revision ID: e5a9d3c82b40
Revises: d4f8c2a71b30
Create Date: 2026-10-01

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e5a9d3c82b40"
down_revision: str | Sequence[str] | None = "d4f8c2a71b30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "formal_quotes",
        sa.Column("shipping_insurance_decision", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "formal_quotes",
        sa.Column(
            "shipping_insurance_decided_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "formal_quotes",
        sa.Column(
            "shipping_insurance_decided_by_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        op.f("ck_formal_quotes_shipping_insurance_decision_valid"),
        "formal_quotes",
        (
            "shipping_insurance_decision IS NULL OR "
            "shipping_insurance_decision IN ('accepted', 'declined')"
        ),
    )
    op.create_check_constraint(
        op.f("ck_formal_quotes_shipping_insurance_evidence_complete"),
        "formal_quotes",
        (
            "((shipping_insurance_decision IS NULL "
            "AND shipping_insurance_decided_at IS NULL "
            "AND shipping_insurance_decided_by_user_id IS NULL) OR "
            "(shipping_insurance_decision IS NOT NULL "
            "AND shipping_insurance_decided_at IS NOT NULL "
            "AND shipping_insurance_decided_by_user_id IS NOT NULL))"
        ),
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_formal_quotes_shipping_insurance_evidence_complete"),
        "formal_quotes",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_formal_quotes_shipping_insurance_decision_valid"),
        "formal_quotes",
        type_="check",
    )
    op.drop_column("formal_quotes", "shipping_insurance_decided_by_user_id")
    op.drop_column("formal_quotes", "shipping_insurance_decided_at")
    op.drop_column("formal_quotes", "shipping_insurance_decision")
