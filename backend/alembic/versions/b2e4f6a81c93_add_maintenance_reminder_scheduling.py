"""add maintenance reminder scheduling

Revision ID: b2e4f6a81c93
Revises: a8d5c3f19b72
Create Date: 2026-09-29

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "b2e4f6a81c93"
down_revision: str | Sequence[str] | None = "a8d5c3f19b72"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    reminder_kind = postgresql.ENUM(
        "filter_replacement",
        "uv_service",
        "product_specific",
        name="reminder_preference_kind",
    )
    reminder_kind.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "product_relationships",
        sa.Column(
            "reminder_preference",
            postgresql.ENUM(
                "filter_replacement",
                "uv_service",
                "product_specific",
                name="reminder_preference_kind",
                create_type=False,
            ),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        op.f("ck_product_relationships_reminder_preference_valid"),
        "product_relationships",
        (
            "reminder_preference IS NULL OR "
            "(is_consumable AND replacement_interval_days IS NOT NULL)"
        ),
    )

    reminder_status = postgresql.ENUM(
        "sent",
        "failed",
        "suppressed",
        name="maintenance_reminder_status",
    )
    reminder_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "maintenance_reminders",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "equipment_id",
            sa.UUID(),
            sa.ForeignKey("customer_equipment.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "related_product_id",
            sa.UUID(),
            sa.ForeignKey("products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "reminder_kind",
            postgresql.ENUM(
                "filter_replacement",
                "uv_service",
                "product_specific",
                name="reminder_preference_kind",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("due_on", sa.Date(), nullable=False),
        sa.Column("recipient", sa.String(length=320), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "sent",
                "failed",
                "suppressed",
                name="maintenance_reminder_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "email_delivery_id",
            sa.UUID(),
            sa.ForeignKey("email_deliveries.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "attempted_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "equipment_id",
            "related_product_id",
            "reminder_kind",
            "due_on",
            name="uq_maintenance_reminder_business_key",
        ),
    )
    op.create_index(
        "ix_maintenance_reminders_due_on",
        "maintenance_reminders",
        ["due_on"],
    )
    op.create_index(
        "ix_maintenance_reminders_user_id",
        "maintenance_reminders",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_maintenance_reminders_user_id",
        table_name="maintenance_reminders",
    )
    op.drop_index(
        "ix_maintenance_reminders_due_on",
        table_name="maintenance_reminders",
    )
    op.drop_table("maintenance_reminders")

    maintenance_status = postgresql.ENUM(
        "sent",
        "failed",
        "suppressed",
        name="maintenance_reminder_status",
    )
    maintenance_status.drop(op.get_bind(), checkfirst=True)

    op.drop_constraint(
        op.f("ck_product_relationships_reminder_preference_valid"),
        "product_relationships",
        type_="check",
    )
    op.drop_column(
        "product_relationships",
        "reminder_preference",
    )

    reminder_kind = postgresql.ENUM(
        "filter_replacement",
        "uv_service",
        "product_specific",
        name="reminder_preference_kind",
    )
    reminder_kind.drop(op.get_bind(), checkfirst=True)
