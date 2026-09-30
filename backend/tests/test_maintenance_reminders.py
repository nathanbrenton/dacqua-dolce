import uuid
from datetime import date
from types import SimpleNamespace

from app.core.email_config import EmailRuntimeSettings
from app.models.catalog import ReminderPreferenceKind
from app.services.maintenance_reminders import (
    MaintenanceReminderCandidate,
    maintenance_reminder_message,
    reminder_preference_enabled,
)


def test_reminder_preferences_map_to_existing_explicit_opt_ins() -> None:
    preferences = SimpleNamespace(
        filter_replacement_reminders=True,
        uv_service_reminders=False,
        product_specific_reminders=True,
    )

    assert reminder_preference_enabled(
        preferences,
        ReminderPreferenceKind.filter_replacement,
    )
    assert not reminder_preference_enabled(
        preferences,
        ReminderPreferenceKind.uv_service,
    )
    assert reminder_preference_enabled(
        preferences,
        ReminderPreferenceKind.product_specific,
    )
    assert not reminder_preference_enabled(
        None,
        ReminderPreferenceKind.product_specific,
    )


def test_maintenance_reminder_email_contains_safe_customer_context() -> None:
    candidate = MaintenanceReminderCandidate(
        user_id=uuid.uuid4(),
        recipient="customer@example.com",
        equipment_id=uuid.uuid4(),
        equipment_name="Origin",
        related_product_id=uuid.uuid4(),
        related_product_name="Replacement Carbon Block",
        related_product_path="/products/replacement-carbon-block",
        reminder_kind=ReminderPreferenceKind.filter_replacement,
        due_on=date(2026, 10, 15),
    )
    settings = EmailRuntimeSettings(
        environment="test",
        public_origin="https://example.test",
        email_provider="disabled",
        email_from="no-reply@example.test",
        email_support_from="support@example.test",
    )

    message = maintenance_reminder_message(
        candidate,
        settings=settings,
    )

    assert message.sender == "support@example.test"
    assert message.recipient == "customer@example.com"
    assert message.reply_to == "support@example.test"
    assert "Origin" in message.body_text
    assert "Replacement Carbon Block" in message.body_text
    assert "2026-10-15" in message.body_text
    assert "https://example.test/account" in message.body_text
    assert "https://example.test/products/replacement-carbon-block" in message.body_text
    assert "card" not in message.body_text.lower()
