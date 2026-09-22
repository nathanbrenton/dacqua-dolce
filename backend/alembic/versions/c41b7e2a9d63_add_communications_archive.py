"""add communications archive

Revision ID: c41b7e2a9d63
Revises: f5c2d8a74e10
Create Date: 2026-09-22

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c41b7e2a9d63"
down_revision: str | Sequence[str] | None = (
    "f5c2d8a74e10"
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


thread_status = sa.Enum(
    "open",
    "closed",
    name="communication_thread_status",
)

direction = sa.Enum(
    "inbound",
    "outbound",
    "internal",
    name="communication_direction",
)

message_status = sa.Enum(
    "draft",
    "queued",
    "sent",
    "received",
    "failed",
    "suppressed",
    name="communication_message_status",
)

recipient_type = sa.Enum(
    "to",
    "cc",
    "bcc",
    "reply_to",
    name="communication_recipient_type",
)


def upgrade() -> None:
    op.create_table(
        "communication_threads",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "customer_user_id",
            sa.UUID(),
            nullable=True,
        ),
        sa.Column(
            "assigned_user_id",
            sa.UUID(),
            nullable=True,
        ),
        sa.Column(
            "subject",
            sa.String(length=300),
            nullable=True,
        ),
        sa.Column(
            "related_entity_type",
            sa.String(length=80),
            nullable=True,
        ),
        sa.Column(
            "related_entity_id",
            sa.String(length=120),
            nullable=True,
        ),
        sa.Column(
            "status",
            thread_status,
            server_default="open",
            nullable=False,
        ),
        sa.Column(
            "last_message_at",
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
            ["assigned_user_id"],
            ["users.id"],
            name=op.f(
                "fk_communication_threads_assigned_user_id_users"
            ),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["customer_user_id"],
            ["users.id"],
            name=op.f(
                "fk_communication_threads_customer_user_id_users"
            ),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_communication_threads"),
        ),
    )

    op.create_index(
        "ix_communication_threads_customer_user_id",
        "communication_threads",
        ["customer_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_communication_threads_assigned_user_id",
        "communication_threads",
        ["assigned_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_communication_threads_status_last_message",
        "communication_threads",
        ["status", "last_message_at"],
        unique=False,
    )

    op.create_table(
        "communication_messages",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "thread_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "author_user_id",
            sa.UUID(),
            nullable=True,
        ),
        sa.Column(
            "email_delivery_id",
            sa.UUID(),
            nullable=True,
        ),
        sa.Column(
            "direction",
            direction,
            nullable=False,
        ),
        sa.Column(
            "status",
            message_status,
            nullable=False,
        ),
        sa.Column(
            "provider",
            sa.String(length=40),
            nullable=True,
        ),
        sa.Column(
            "provider_message_id",
            sa.String(length=300),
            nullable=True,
        ),
        sa.Column(
            "message_stream",
            sa.String(length=80),
            nullable=True,
        ),
        sa.Column(
            "internet_message_id",
            sa.String(length=500),
            nullable=True,
        ),
        sa.Column(
            "in_reply_to",
            sa.String(length=500),
            nullable=True,
        ),
        sa.Column(
            "sender_address",
            sa.String(length=320),
            nullable=False,
        ),
        sa.Column(
            "sender_name",
            sa.String(length=200),
            nullable=True,
        ),
        sa.Column(
            "subject",
            sa.String(length=300),
            nullable=False,
        ),
        sa.Column(
            "body_text",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "body_html",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "content_redacted",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "received_at",
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
            ["author_user_id"],
            ["users.id"],
            name=op.f(
                "fk_communication_messages_author_user_id_users"
            ),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["email_delivery_id"],
            ["email_deliveries.id"],
            name=op.f(
                "fk_communication_messages_email_delivery_id_email_deliveries"
            ),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["thread_id"],
            ["communication_threads.id"],
            name=op.f(
                "fk_communication_messages_thread_id_communication_threads"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_communication_messages"),
        ),
        sa.UniqueConstraint(
            "email_delivery_id",
            name=(
                "uq_communication_messages_"
                "email_delivery_id"
            ),
        ),
        sa.UniqueConstraint(
            "provider",
            "provider_message_id",
            name=(
                "uq_communication_messages_"
                "provider_message_id"
            ),
        ),
    )

    op.create_index(
        "ix_communication_messages_thread_created",
        "communication_messages",
        ["thread_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_communication_messages_direction_status",
        "communication_messages",
        ["direction", "status"],
        unique=False,
    )

    op.create_table(
        "communication_recipients",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "message_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "recipient_type",
            recipient_type,
            nullable=False,
        ),
        sa.Column(
            "address",
            sa.String(length=320),
            nullable=False,
        ),
        sa.Column(
            "display_name",
            sa.String(length=200),
            nullable=True,
        ),
        sa.Column(
            "position",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["communication_messages.id"],
            name=op.f(
                "fk_communication_recipients_message_id_communication_messages"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f(
                "pk_communication_recipients"
            ),
        ),
        sa.UniqueConstraint(
            "message_id",
            "recipient_type",
            "address",
            name=(
                "uq_communication_recipients_"
                "message_type_address"
            ),
        ),
    )

    op.create_index(
        "ix_communication_recipients_message_type",
        "communication_recipients",
        ["message_id", "recipient_type"],
        unique=False,
    )

    op.create_table(
        "communication_attachments",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "message_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "provider_attachment_id",
            sa.String(length=300),
            nullable=True,
        ),
        sa.Column(
            "filename",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column(
            "content_type",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "content_id",
            sa.String(length=500),
            nullable=True,
        ),
        sa.Column(
            "content_disposition",
            sa.String(length=40),
            nullable=True,
        ),
        sa.Column(
            "size_bytes",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "sha256",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "content",
            sa.LargeBinary(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["communication_messages.id"],
            name=op.f(
                "fk_communication_attachments_message_id_communication_messages"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f(
                "pk_communication_attachments"
            ),
        ),
    )

    op.create_index(
        "ix_communication_attachments_message_id",
        "communication_attachments",
        ["message_id"],
        unique=False,
    )

    op.create_table(
        "communication_events",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "message_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "provider",
            sa.String(length=40),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            sa.String(length=80),
            nullable=False,
        ),
        sa.Column(
            "provider_event_id",
            sa.String(length=300),
            nullable=True,
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "details",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["communication_messages.id"],
            name=op.f(
                "fk_communication_events_message_id_communication_messages"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_communication_events"),
        ),
        sa.UniqueConstraint(
            "provider",
            "provider_event_id",
            name=(
                "uq_communication_events_"
                "provider_event_id"
            ),
        ),
    )

    op.create_index(
        "ix_communication_events_message_occurred",
        "communication_events",
        ["message_id", "occurred_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_communication_events_message_occurred",
        table_name="communication_events",
    )
    op.drop_table("communication_events")

    op.drop_index(
        "ix_communication_attachments_message_id",
        table_name="communication_attachments",
    )
    op.drop_table("communication_attachments")

    op.drop_index(
        "ix_communication_recipients_message_type",
        table_name="communication_recipients",
    )
    op.drop_table("communication_recipients")

    op.drop_index(
        "ix_communication_messages_direction_status",
        table_name="communication_messages",
    )
    op.drop_index(
        "ix_communication_messages_thread_created",
        table_name="communication_messages",
    )
    op.drop_table("communication_messages")

    op.drop_index(
        "ix_communication_threads_status_last_message",
        table_name="communication_threads",
    )
    op.drop_index(
        "ix_communication_threads_assigned_user_id",
        table_name="communication_threads",
    )
    op.drop_index(
        "ix_communication_threads_customer_user_id",
        table_name="communication_threads",
    )
    op.drop_table("communication_threads")

    bind = op.get_bind()
    recipient_type.drop(bind, checkfirst=True)
    message_status.drop(bind, checkfirst=True)
    direction.drop(bind, checkfirst=True)
    thread_status.drop(bind, checkfirst=True)
