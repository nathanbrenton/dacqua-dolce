from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.operations import PromotionCreateRequest


def test_promotion_window_accepts_timezone_aware_range() -> None:
    start = datetime.now(UTC) + timedelta(hours=1)
    payload = PromotionCreateRequest(
        amount_minor=9900,
        effective_from=start,
        effective_until=start + timedelta(days=2),
    )
    assert payload.amount_minor == 9900


def test_promotion_window_rejects_non_positive_amount() -> None:
    start = datetime.now(UTC) + timedelta(hours=1)
    with pytest.raises(ValidationError):
        PromotionCreateRequest(
            amount_minor=0,
            effective_from=start,
            effective_until=start + timedelta(days=1),
        )


def test_promotion_window_rejects_naive_timestamps() -> None:
    start = datetime.now().replace(microsecond=0)
    with pytest.raises(ValidationError, match="timezone"):
        PromotionCreateRequest(
            amount_minor=9900,
            effective_from=start,
            effective_until=start + timedelta(days=1),
        )


def test_promotion_window_rejects_end_before_start() -> None:
    start = datetime.now(UTC) + timedelta(hours=1)
    with pytest.raises(ValidationError, match="after its start"):
        PromotionCreateRequest(
            amount_minor=9900,
            effective_from=start,
            effective_until=start,
        )
