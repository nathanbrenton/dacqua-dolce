from datetime import date

from app.services.post_purchase import next_replacement_due_on


def test_replacement_due_uses_last_service_when_available() -> None:
    due_on = next_replacement_due_on(
        installed_on=date(2026, 1, 1),
        last_service_on=date(2026, 6, 1),
        replacement_interval_days=180,
    )

    assert due_on == date(2026, 11, 28)


def test_replacement_due_falls_back_to_installation_date() -> None:
    due_on = next_replacement_due_on(
        installed_on=date(2026, 1, 1),
        last_service_on=None,
        replacement_interval_days=180,
    )

    assert due_on == date(2026, 6, 30)


def test_replacement_due_is_unscheduled_without_interval_or_baseline() -> None:
    assert next_replacement_due_on(
        installed_on=date(2026, 1, 1),
        last_service_on=None,
        replacement_interval_days=None,
    ) is None
    assert next_replacement_due_on(
        installed_on=None,
        last_service_on=None,
        replacement_interval_days=180,
    ) is None
