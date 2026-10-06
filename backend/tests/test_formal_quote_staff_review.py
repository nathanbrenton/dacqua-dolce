import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.quote import FormalQuoteStatus
from app.services.formal_quotes import (
    STAFF_REVIEW_REASON_ASSISTED_SALE,
    STAFF_REVIEW_REASON_MANUAL_COMPLEX,
    complete_formal_quote_staff_review,
    formal_quote_staff_review_reasons,
    present_formal_quote,
)


class ProductDatabase:
    def __init__(self, products: dict[uuid.UUID, object]) -> None:
        self.products = products

    def get(self, model: object, identifier: object) -> object | None:
        return self.products.get(identifier)


def test_assisted_sale_product_requires_staff_review() -> None:
    product_id = uuid.uuid4()
    db = ProductDatabase(
        {
            product_id: SimpleNamespace(
                id=product_id,
                assisted_sale_required=True,
            )
        }
    )

    reasons = formal_quote_staff_review_reasons(
        db,  # type: ignore[arg-type]
        lines=[
            SimpleNamespace(
                product_id=product_id,
            )
        ],
        manual_staff_review_required=False,
    )

    assert reasons == [STAFF_REVIEW_REASON_ASSISTED_SALE]


def test_manual_complex_review_adds_reason_without_amount_threshold() -> None:
    product_id = uuid.uuid4()
    db = ProductDatabase(
        {
            product_id: SimpleNamespace(
                id=product_id,
                assisted_sale_required=False,
            )
        }
    )

    reasons = formal_quote_staff_review_reasons(
        db,  # type: ignore[arg-type]
        lines=[
            SimpleNamespace(
                product_id=product_id,
            )
        ],
        manual_staff_review_required=True,
    )

    assert reasons == [STAFF_REVIEW_REASON_MANUAL_COMPLEX]


def test_pending_staff_review_blocks_presentation() -> None:
    quote = SimpleNamespace(
        status=FormalQuoteStatus.draft,
        staff_review_required=True,
        staff_review_completed_at=None,
    )

    with pytest.raises(HTTPException) as exc:
        present_formal_quote(
            SimpleNamespace(),  # type: ignore[arg-type]
            formal_quote=quote,  # type: ignore[arg-type]
            actor_user=SimpleNamespace(id=uuid.uuid4()),  # type: ignore[arg-type]
        )

    assert exc.value.status_code == 409
    assert "staff review" in str(exc.value.detail).lower()


def test_staff_review_completion_records_actor_and_audit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded: list[dict[str, object]] = []

    def record_event(db: object, **kwargs: object) -> None:
        recorded.append(kwargs)

    monkeypatch.setattr(
        "app.services.formal_quotes.record_audit_event",
        record_event,
    )
    actor_id = uuid.uuid4()
    quote = SimpleNamespace(
        id=uuid.uuid4(),
        quote_request_id=uuid.uuid4(),
        revision_number=3,
        status=FormalQuoteStatus.draft,
        staff_review_required=True,
        staff_review_reasons=[STAFF_REVIEW_REASON_ASSISTED_SALE],
        staff_review_completed_at=None,
        staff_review_completed_by_user_id=None,
    )

    result = complete_formal_quote_staff_review(
        SimpleNamespace(),  # type: ignore[arg-type]
        formal_quote=quote,  # type: ignore[arg-type]
        actor_user=SimpleNamespace(id=actor_id),  # type: ignore[arg-type]
    )

    assert result.staff_review_completed_at is not None
    assert result.staff_review_completed_by_user_id == actor_id
    assert recorded[0]["action"] == "formal_quote.staff_review_completed"
    assert recorded[0]["actor_user_id"] == actor_id


def test_staff_review_completion_rejects_unrequired_quote() -> None:
    quote = SimpleNamespace(
        status=FormalQuoteStatus.draft,
        staff_review_required=False,
    )

    with pytest.raises(HTTPException) as exc:
        complete_formal_quote_staff_review(
            SimpleNamespace(),  # type: ignore[arg-type]
            formal_quote=quote,  # type: ignore[arg-type]
            actor_user=SimpleNamespace(id=uuid.uuid4()),  # type: ignore[arg-type]
        )

    assert exc.value.status_code == 409
