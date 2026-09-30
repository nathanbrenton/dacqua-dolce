from datetime import UTC, date, datetime

from app.services.calendar_export import build_all_day_ics


def test_all_day_ics_uses_one_day_window_and_escapes_text() -> None:
    payload = build_all_day_ics(
        uid="replacement:test@example.com",
        summary="Replace Filter, Stage 1",
        event_date=date(2026, 10, 15),
        description="Review; then replace\\clean.",
        url="https://dacquadolce.com/account",
        generated_at=datetime(2026, 9, 29, 20, 0, tzinfo=UTC),
    )

    assert "DTSTART;VALUE=DATE:20261015" in payload
    assert "DTEND;VALUE=DATE:20261016" in payload
    assert "DTSTAMP:20260929T200000Z" in payload
    assert "SUMMARY:Replace Filter\\, Stage 1" in payload
    assert "DESCRIPTION:Review\\; then replace\\\\clean." in payload
    assert "URL:https://dacquadolce.com/account" in payload
    assert payload.endswith("\r\n")
