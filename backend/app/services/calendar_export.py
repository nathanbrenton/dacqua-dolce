from __future__ import annotations

from datetime import UTC, date, datetime, timedelta


def _escape_ics_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def build_all_day_ics(
    *,
    uid: str,
    summary: str,
    event_date: date,
    description: str,
    url: str | None = None,
    generated_at: datetime | None = None,
) -> str:
    stamp = generated_at or datetime.now(UTC)
    end_date = event_date + timedelta(days=1)

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//D'Acqua Dolce//Customer Service Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{_escape_ics_text(uid)}",
        f"DTSTAMP:{stamp.astimezone(UTC).strftime('%Y%m%dT%H%M%SZ')}",
        f"DTSTART;VALUE=DATE:{event_date.strftime('%Y%m%d')}",
        f"DTEND;VALUE=DATE:{end_date.strftime('%Y%m%d')}",
        f"SUMMARY:{_escape_ics_text(summary)}",
        f"DESCRIPTION:{_escape_ics_text(description)}",
    ]

    if url is not None:
        lines.append(f"URL:{_escape_ics_text(url)}")

    lines.extend(
        (
            "END:VEVENT",
            "END:VCALENDAR",
            "",
        )
    )
    return "\r\n".join(lines)
