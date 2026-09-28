from types import SimpleNamespace

from app.api.account import communication_preferences_read
from app.schemas.account import (
    CommunicationPreferencesRead,
    CommunicationPreferencesUpdate,
)


def test_communication_preferences_default_to_opt_out() -> None:
    payload = CommunicationPreferencesRead().model_dump()

    assert payload
    assert all(value is False for value in payload.values())


def test_communication_preferences_are_explicit_booleans() -> None:
    payload = CommunicationPreferencesUpdate(
        filter_replacement_reminders=True,
        uv_service_reminders=True,
    )

    assert payload.filter_replacement_reminders is True
    assert payload.uv_service_reminders is True
    assert payload.softener_check_reminders is False


def test_preferences_read_maps_persisted_state() -> None:
    persisted = SimpleNamespace(
        filter_replacement_reminders=True,
        softener_check_reminders=False,
        uv_service_reminders=True,
        annual_system_check_reminders=False,
        product_specific_reminders=True,
        post_purchase_followup=False,
        post_installation_followup=True,
    )

    payload = communication_preferences_read(persisted).model_dump()

    assert payload["filter_replacement_reminders"] is True
    assert payload["post_installation_followup"] is True
    assert payload["softener_check_reminders"] is False
