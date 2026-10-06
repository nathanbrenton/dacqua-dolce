"""Tests for scheduled public catalog retirement."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.services.catalog_publication import product_is_publicly_visible


def product(*, active: bool = True, public_retire_at=None):
    return SimpleNamespace(active=active, public_retire_at=public_retire_at)


def test_active_product_without_retirement_stays_public() -> None:
    assert product_is_publicly_visible(product()) is True


def test_inactive_product_is_not_public() -> None:
    assert product_is_publicly_visible(product(active=False)) is False


def test_future_retirement_stays_public_until_timestamp() -> None:
    now = datetime(2026, 10, 5, 20, 0, tzinfo=UTC)
    item = product(public_retire_at=now + timedelta(days=30))

    assert product_is_publicly_visible(item, now=now) is True


def test_retirement_hides_product_at_timestamp() -> None:
    now = datetime(2026, 10, 5, 20, 0, tzinfo=UTC)
    item = product(public_retire_at=now)

    assert product_is_publicly_visible(item, now=now) is False


def test_naive_retirement_timestamp_fails_closed() -> None:
    item = product(public_retire_at=datetime(2026, 10, 5, 20, 0))

    with pytest.raises(ValueError):
        product_is_publicly_visible(item)
