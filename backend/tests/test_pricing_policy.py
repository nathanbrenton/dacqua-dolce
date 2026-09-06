from datetime import UTC, datetime, timedelta

from app.models.catalog import (
    PricingPolicyMode,
    ProductPrice,
)
from app.services.pricing import (
    resolve_pricing,
    select_effective_price,
)


def make_price(
    mode: PricingPolicyMode,
    *,
    amount_minor: int | None = 12500,
) -> ProductPrice:
    return ProductPrice(
        pricing_policy_mode=mode,
        amount_minor=amount_minor,
        currency="USD",
        effective_from=datetime.now(UTC) - timedelta(minutes=1),
        active=True,
    )


def test_public_price_is_displayable() -> None:
    decision = resolve_pricing(make_price(PricingPolicyMode.PUBLIC))

    assert decision.display_price is True
    assert decision.amount_minor == 12500
    assert decision.can_add_to_cart is True


def test_cart_only_price_is_not_public() -> None:
    decision = resolve_pricing(make_price(PricingPolicyMode.CART_ONLY))

    assert decision.display_price is False
    assert decision.amount_minor is None
    assert decision.can_add_to_cart is True


def test_no_online_sale_blocks_cart_and_price() -> None:
    decision = resolve_pricing(make_price(PricingPolicyMode.NO_ONLINE_SALE))

    assert decision.display_price is False
    assert decision.can_add_to_cart is False
    assert decision.can_checkout_online is False


def test_login_required_is_hidden_anonymously() -> None:
    price = make_price(PricingPolicyMode.LOGIN_REQUIRED)

    anonymous = resolve_pricing(
        price,
        authenticated=False,
    )

    authenticated = resolve_pricing(
        price,
        authenticated=True,
    )

    assert anonymous.display_price is False
    assert anonymous.action == "SIGN_IN"
    assert authenticated.display_price is True
    assert authenticated.amount_minor == 12500


def test_missing_price_is_conservative() -> None:
    decision = resolve_pricing(None)

    assert decision.mode == PricingPolicyMode.NO_ONLINE_PRICE
    assert decision.display_price is False
    assert decision.can_add_to_cart is False


def test_effective_price_selects_latest_record() -> None:
    now = datetime.now(UTC)

    older = make_price(PricingPolicyMode.PUBLIC)
    older.effective_from = now - timedelta(days=2)

    latest = make_price(
        PricingPolicyMode.PRIVATE_QUOTE,
        amount_minor=None,
    )
    latest.effective_from = now - timedelta(days=1)

    selected = select_effective_price(
        [older, latest],
        now=now,
    )

    assert selected is latest
