import pytest
from pydantic import ValidationError

from app.models.catalog import (
    InventoryStatus,
    PricingPolicyMode,
)
from app.schemas.operations import (
    InventoryUpdateRequest,
    PricingUpdateRequest,
    QuoteNotesUpdate,
)


@pytest.mark.parametrize(
    "mode",
    [
        PricingPolicyMode.PUBLIC,
        PricingPolicyMode.MAP_LIMITED,
        PricingPolicyMode.CART_ONLY,
        PricingPolicyMode.LOGIN_REQUIRED,
    ],
)
def test_price_amount_required_for_online_purchase_modes(
    mode: PricingPolicyMode,
) -> None:
    with pytest.raises(ValidationError):
        PricingUpdateRequest(
            mode=mode,
            amount_minor=None,
            currency="USD",
        )


@pytest.mark.parametrize(
    "mode",
    [
        PricingPolicyMode.PRIVATE_QUOTE,
        PricingPolicyMode.NO_ONLINE_PRICE,
        PricingPolicyMode.NO_ONLINE_SALE,
    ],
)
def test_restricted_modes_reject_online_amount(
    mode: PricingPolicyMode,
) -> None:
    with pytest.raises(ValidationError):
        PricingUpdateRequest(
            mode=mode,
            amount_minor=10000,
            currency="USD",
        )


def test_currency_is_normalized() -> None:
    payload = PricingUpdateRequest(
        mode=PricingPolicyMode.PUBLIC,
        amount_minor=10000,
        currency="usd",
    )

    assert payload.currency == "USD"


def test_inventory_reserved_is_not_operator_editable() -> None:
    with pytest.raises(ValidationError):
        InventoryUpdateRequest(
            status=InventoryStatus.in_stock,
            quantity_on_hand=1,
            quantity_reserved=1,
        )

def test_quote_notes_are_trimmed() -> None:
    payload = QuoteNotesUpdate(
        internal_notes="  Called customer; awaiting reply.  ",
    )

    assert payload.internal_notes == (
        "Called customer; awaiting reply."
    )


def test_blank_quote_notes_become_none() -> None:
    payload = QuoteNotesUpdate(
        internal_notes="   ",
    )

    assert payload.internal_notes is None


def test_quote_notes_have_reasonable_limit() -> None:
    with pytest.raises(ValidationError):
        QuoteNotesUpdate(
            internal_notes="x" * 8001,
        )
