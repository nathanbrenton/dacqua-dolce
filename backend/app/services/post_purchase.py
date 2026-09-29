from datetime import date, timedelta


def next_replacement_due_on(
    *,
    installed_on: date | None,
    last_service_on: date | None,
    replacement_interval_days: int | None,
) -> date | None:
    if replacement_interval_days is None:
        return None

    baseline = last_service_on or installed_on
    if baseline is None:
        return None

    return baseline + timedelta(days=replacement_interval_days)
