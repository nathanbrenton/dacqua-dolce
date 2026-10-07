from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from app.services import order_reviews


class ReviewDatabase:
    def __init__(self) -> None:
        self.flush_count = 0

    def flush(self) -> None:
        self.flush_count += 1


def pending_order() -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        review_customer_contact_reviewed=False,
        review_supplier_availability_verified=False,
        review_whole_order_reviewed=False,
        review_customer_contact_required=False,
        review_customer_contact_completed=False,
        reviewed_by_user_id=None,
        reviewed_at=None,
        review_on_hold=False,
        review_hold_reason=None,
        review_proposed_alternative=None,
        review_hold_started_by_user_id=None,
        review_hold_started_at=None,
        review_hold_released_by_user_id=None,
        review_hold_released_at=None,
        review_customer_response_note=None,
    )


def test_complete_review_requires_short_checklist(monkeypatch: Any) -> None:
    database = ReviewDatabase()
    target = pending_order()
    monkeypatch.setattr(order_reviews, "record_audit_event", lambda *args, **kwargs: None)

    with pytest.raises(order_reviews.OrderReviewError, match="supplier availability"):
        order_reviews.update_order_review(
            database,  # type: ignore[arg-type]
            order=target,  # type: ignore[arg-type]
            actor_user_id=uuid.uuid4(),
            customer_contact_reviewed=True,
            supplier_availability_verified=False,
            whole_order_reviewed=True,
            customer_contact_required=False,
            customer_contact_completed=False,
            complete=True,
        )


def test_required_customer_contact_must_be_completed(monkeypatch: Any) -> None:
    database = ReviewDatabase()
    target = pending_order()
    monkeypatch.setattr(order_reviews, "record_audit_event", lambda *args, **kwargs: None)

    with pytest.raises(order_reviews.OrderReviewError, match="required customer contact"):
        order_reviews.update_order_review(
            database,  # type: ignore[arg-type]
            order=target,  # type: ignore[arg-type]
            actor_user_id=uuid.uuid4(),
            customer_contact_reviewed=True,
            supplier_availability_verified=True,
            whole_order_reviewed=True,
            customer_contact_required=True,
            customer_contact_completed=False,
            complete=True,
        )


def test_completed_review_records_reviewer_and_time(monkeypatch: Any) -> None:
    database = ReviewDatabase()
    target = pending_order()
    actor = uuid.uuid4()
    now = datetime(2026, 10, 7, 16, 30, tzinfo=UTC)
    audits: list[dict[str, object]] = []
    monkeypatch.setattr(
        order_reviews,
        "record_audit_event",
        lambda *args, **kwargs: audits.append(kwargs),
    )

    order_reviews.update_order_review(
        database,  # type: ignore[arg-type]
        order=target,  # type: ignore[arg-type]
        actor_user_id=actor,
        customer_contact_reviewed=True,
        supplier_availability_verified=True,
        whole_order_reviewed=True,
        customer_contact_required=False,
        customer_contact_completed=False,
        complete=True,
        now=now,
    )

    assert target.reviewed_by_user_id == actor
    assert target.reviewed_at == now
    assert audits[0]["action"] == "order.review_completed"


def test_hold_records_alternative_without_substitution(monkeypatch: Any) -> None:
    database = ReviewDatabase()
    target = pending_order()
    actor = uuid.uuid4()
    audits: list[dict[str, object]] = []
    monkeypatch.setattr(
        order_reviews,
        "record_audit_event",
        lambda *args, **kwargs: audits.append(kwargs),
    )

    order_reviews.place_order_on_hold(
        database,  # type: ignore[arg-type]
        order=target,  # type: ignore[arg-type]
        actor_user_id=actor,
        reason="Supplier cannot fulfill the selected configuration.",
        proposed_alternative="Offer the customer the compatible alternate configuration.",
    )

    assert target.review_on_hold is True
    assert target.review_customer_contact_required is True
    assert target.review_customer_contact_completed is False
    assert target.review_proposed_alternative.startswith("Offer the customer")
    assert audits[0]["metadata"]["automatic_substitution"] is False


def test_release_hold_requires_and_records_customer_response(monkeypatch: Any) -> None:
    database = ReviewDatabase()
    target = pending_order()
    target.review_on_hold = True
    target.review_hold_reason = "Unavailable"
    target.review_proposed_alternative = "Alternative"
    monkeypatch.setattr(order_reviews, "record_audit_event", lambda *args, **kwargs: None)

    order_reviews.release_order_hold(
        database,  # type: ignore[arg-type]
        order=target,  # type: ignore[arg-type]
        actor_user_id=uuid.uuid4(),
        customer_response_note="Customer approved the proposed alternative.",
    )

    assert target.review_on_hold is False
    assert target.review_customer_contact_completed is True
    assert target.review_customer_response_note.startswith("Customer approved")
