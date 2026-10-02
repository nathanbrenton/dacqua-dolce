"""add shipping insurance charge kind

Revision ID: d4f8c2a71b30
Revises: c3e7a1f49b20
Create Date: 2026-10-01

"""

from collections.abc import Sequence

from alembic import op

revision: str = "d4f8c2a71b30"
down_revision: str | Sequence[str] | None = "c3e7a1f49b20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_NEW_KIND_CHECK = (
    "kind IN ('shipping', 'shipping_insurance', 'tax', 'installation', "
    "'discount', 'other_charge', 'other_credit')"
)
_NEW_SIGN_CHECK = (
    "((kind IN ('shipping', 'shipping_insurance', 'tax', 'installation', "
    "'other_charge') AND amount_minor > 0) OR "
    "(kind IN ('discount', 'other_credit') AND amount_minor < 0))"
)
_OLD_KIND_CHECK = (
    "kind IN ('shipping', 'tax', 'installation', 'discount', "
    "'other_charge', 'other_credit')"
)
_OLD_SIGN_CHECK = (
    "((kind IN ('shipping', 'tax', 'installation', 'other_charge') "
    "AND amount_minor > 0) OR "
    "(kind IN ('discount', 'other_credit') AND amount_minor < 0))"
)


def _replace_charge_constraints(
    *,
    table: str,
    prefix: str,
    kind_check: str,
    sign_check: str,
) -> None:
    op.drop_constraint(
        op.f(f"ck_{table}_{prefix}_kind_valid"),
        table,
        type_="check",
    )
    op.drop_constraint(
        op.f(f"ck_{table}_{prefix}_amount_sign_valid"),
        table,
        type_="check",
    )
    op.create_check_constraint(
        op.f(f"ck_{table}_{prefix}_kind_valid"),
        table,
        kind_check,
    )
    op.create_check_constraint(
        op.f(f"ck_{table}_{prefix}_amount_sign_valid"),
        table,
        sign_check,
    )


def upgrade() -> None:
    _replace_charge_constraints(
        table="formal_quote_charges",
        prefix="formal_quote_charges",
        kind_check=_NEW_KIND_CHECK,
        sign_check=_NEW_SIGN_CHECK,
    )
    _replace_charge_constraints(
        table="order_charges",
        prefix="order_charges",
        kind_check=_NEW_KIND_CHECK,
        sign_check=_NEW_SIGN_CHECK,
    )


def downgrade() -> None:
    _replace_charge_constraints(
        table="order_charges",
        prefix="order_charges",
        kind_check=_OLD_KIND_CHECK,
        sign_check=_OLD_SIGN_CHECK,
    )
    _replace_charge_constraints(
        table="formal_quote_charges",
        prefix="formal_quote_charges",
        kind_check=_OLD_KIND_CHECK,
        sign_check=_OLD_SIGN_CHECK,
    )
