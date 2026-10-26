"""PT54-B: line-scoped, server-authoritative neoprene pricing and review boundaries."""
import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.models.quote import CommercialChargeKind
from app.schemas.operations import FormalQuoteItemCreate
from app.services.formal_quotes import (
    BLACK_NEOPRENE_JACKET_UNIT_AMOUNT_MINOR,
    NEOPRENE_ELIGIBLE_SKUS,
    STAFF_REVIEW_REASON_JACKET_TAX,
    FormalQuoteLineInput,
    black_neoprene_jacket_charge,
    formal_quote_staff_review_reasons,
)


def test_price_is_authoritative_100_dollars_per_system() -> None:
    assert BLACK_NEOPRENE_JACKET_UNIT_AMOUNT_MINOR == 10_000
    for sku in NEOPRENE_ELIGIBLE_SKUS:
        charge = black_neoprene_jacket_charge(
            product_sku=sku, line_number=2, quantity=3, selected=True
        )
        assert charge is not None
        assert charge.kind is CommercialChargeKind.other_charge
        assert charge.amount_minor == 30_000
        assert sku in charge.label
        assert "line 2" in charge.label
        assert "$100" in charge.label


def test_two_jacket_lines_have_independent_quantity_amounts() -> None:
    a = black_neoprene_jacket_charge(
        product_sku="DD15SOFT", line_number=1, quantity=2, selected=True
    )
    b = black_neoprene_jacket_charge(
        product_sku="DD20CATRV", line_number=2, quantity=1, selected=True
    )
    assert a is not None and b is not None
    assert (a.amount_minor, b.amount_minor) == (20_000, 10_000)
    assert a.label != b.label


def test_no_jacket_means_no_charge_even_for_origin() -> None:
    assert black_neoprene_jacket_charge(
        product_sku="DD6ROAE", line_number=1, quantity=2, selected=False
    ) is None


@pytest.mark.parametrize("sku", ["DD5RO", "DD6ROAE", "UNLISTED", "DD20CLEARPL2"])
def test_noneligible_product_cannot_request_jacket(sku: str) -> None:
    with pytest.raises(HTTPException) as error:
        black_neoprene_jacket_charge(
            product_sku=sku, line_number=1, quantity=1, selected=True
        )
    assert error.value.status_code == 422


@pytest.mark.parametrize("quantity", [0, -1, 101, True])
def test_invalid_quantity_rejected(quantity: object) -> None:
    with pytest.raises(HTTPException) as error:
        black_neoprene_jacket_charge(
            product_sku="DD15SOFT", line_number=1,
            quantity=quantity, selected=True,  # type: ignore[arg-type]
        )
    assert error.value.status_code == 422


def test_schema_flag_is_strict_and_defaults_off() -> None:
    item = FormalQuoteItemCreate(product_id=uuid.uuid4())
    assert item.neoprene_jacket is False
    enabled = FormalQuoteItemCreate(product_id=uuid.uuid4(), neoprene_jacket=True)
    assert enabled.neoprene_jacket is True
    with pytest.raises(ValidationError):
        FormalQuoteItemCreate.model_validate({
            "product_id": str(uuid.uuid4()), "neoprene_jacket": "yes",
        })
    with pytest.raises(ValidationError):
        FormalQuoteItemCreate.model_validate({
            "product_id": str(uuid.uuid4()), "neoprene_jacket": True,
            "neoprene_jacket_amount_minor": 1,
        })


def test_jacket_always_requires_staff_tax_review() -> None:
    # Even if a test product doesn't otherwise require assisted sales,
    # the unresolved jacket tax classification must request staff review.
    class Db:
        def get(self, _model: object, _ident: object) -> object:
            return SimpleNamespace(assisted_sale_required=False)

    lines = [FormalQuoteLineInput(
        product_id=uuid.uuid4(), variant_id=None,
        quantity=1, unit_amount_minor=None, neoprene_jacket=True,
    )]
    reasons = formal_quote_staff_review_reasons(
        Db(),  # type: ignore[arg-type]
        lines=lines, manual_staff_review_required=False,
    )
    assert STAFF_REVIEW_REASON_JACKET_TAX in reasons


def test_existing_lines_need_not_send_jacket_field() -> None:
    line = FormalQuoteLineInput(
        product_id=uuid.uuid4(), variant_id=None,
        quantity=1, unit_amount_minor=None,
    )
    assert line.neoprene_jacket is False
