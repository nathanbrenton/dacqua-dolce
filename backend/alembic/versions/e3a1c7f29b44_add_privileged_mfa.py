"""add privileged MFA

Revision ID: e3a1c7f29b44
Revises: d7b2a4e6c901
Create Date: 2026-09-12

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e3a1c7f29b44"
down_revision: str | Sequence[str] | None = (
    "d7b2a4e6c901"
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_sessions",
        sa.Column(
            "mfa_verified_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.create_table(
        "user_mfa",
        sa.Column(
            "user_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "totp_secret_ciphertext",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "enabled_at",
            sa.DateTime(timezone=True),
            nullable=True,
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
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f(
                "fk_user_mfa_user_id_users"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "user_id",
            name=op.f("pk_user_mfa"),
        ),
    )

    op.create_table(
        "user_mfa_recovery_codes",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "code_hash",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "used_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f(
                "fk_user_mfa_recovery_codes_user_id_users"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f(
                "pk_user_mfa_recovery_codes"
            ),
        ),
    )

    op.create_index(
        "ix_user_mfa_recovery_user_hash",
        "user_mfa_recovery_codes",
        [
            "user_id",
            "code_hash",
        ],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_mfa_recovery_user_hash",
        table_name=(
            "user_mfa_recovery_codes"
        ),
    )
    op.drop_table(
        "user_mfa_recovery_codes"
    )
    op.drop_table("user_mfa")
    op.drop_column(
        "user_sessions",
        "mfa_verified_at",
    )
