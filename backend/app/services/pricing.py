from dataclasses import dataclass
from datetime import UTC, datetime

from app.models.catalog import (
    PricingPolicyMode,
    ProductPrice,
)


@dataclass(frozen=True)
class PricingDecision:
    mode: PricingPolicyMode
    amount_minor: int | None
    currency: str | None
    display_price: bool
    can_add_to_cart: bool
    can_checkout_online: bool
    action: str
    action_label: str


def select_effective_price(
    prices: list[ProductPrice],
    *,
    now: datetime | None = None,
    variant_id: object | None = None,
) -> ProductPrice | None:
    effective_now = now or datetime.now(UTC)

    candidates = [
        price
        for price in prices
        if price.active
        and price.variant_id == variant_id
        and price.effective_from <= effective_now
        and (price.effective_until is None or price.effective_until > effective_now)
    ]

    if not candidates:
        return None

    # A finite pricing window is an intentional temporary override (for example,
    # a promotion). Prefer it over the open-ended standard price while the
    # window is effective, even if the standard price was edited more recently.
    return max(
        candidates,
        key=lambda price: (
            price.effective_until is not None,
            price.effective_from,
        ),
    )


def select_standard_price(
    prices: list[ProductPrice],
    *,
    now: datetime | None = None,
    variant_id: object | None = None,
) -> ProductPrice | None:
    effective_now = now or datetime.now(UTC)
    candidates = [
        price
        for price in prices
        if price.active
        and price.variant_id == variant_id
        and price.effective_until is None
        and price.effective_from <= effective_now
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda price: price.effective_from)


def promotion_mode_supported(mode: PricingPolicyMode) -> bool:
    return mode in {
        PricingPolicyMode.PUBLIC,
        PricingPolicyMode.CART_ONLY,
        PricingPolicyMode.LOGIN_REQUIRED,
    }


def promotion_windows_overlap(
    *,
    existing_from: datetime,
    existing_until: datetime,
    proposed_from: datetime,
    proposed_until: datetime,
) -> bool:
    return existing_from < proposed_until and existing_until > proposed_from


def resolve_pricing(
    price: ProductPrice | None,
    *,
    authenticated: bool = False,
) -> PricingDecision:
    if price is None:
        return PricingDecision(
            mode=PricingPolicyMode.NO_ONLINE_PRICE,
            amount_minor=None,
            currency=None,
            display_price=False,
            can_add_to_cart=False,
            can_checkout_online=False,
            action="REQUEST_QUOTE",
            action_label="Request a Quote",
        )

    mode = price.pricing_policy_mode

    if mode in {
        PricingPolicyMode.PUBLIC,
        PricingPolicyMode.MAP_LIMITED,
    }:
        return PricingDecision(
            mode=mode,
            amount_minor=price.amount_minor,
            currency=price.currency,
            display_price=price.amount_minor is not None,
            can_add_to_cart=True,
            can_checkout_online=True,
            action="ADD_TO_CART",
            action_label="Add to Cart",
        )

    if mode == PricingPolicyMode.CART_ONLY:
        return PricingDecision(
            mode=mode,
            amount_minor=None,
            currency=price.currency,
            display_price=False,
            can_add_to_cart=True,
            can_checkout_online=True,
            action="ADD_TO_CART",
            action_label="Add to Cart",
        )

    if mode == PricingPolicyMode.PRIVATE_QUOTE:
        return PricingDecision(
            mode=mode,
            amount_minor=None,
            currency=price.currency,
            display_price=False,
            can_add_to_cart=False,
            can_checkout_online=False,
            action="REQUEST_QUOTE",
            action_label="Request a Quote",
        )

    if mode == PricingPolicyMode.LOGIN_REQUIRED:
        if authenticated:
            return PricingDecision(
                mode=mode,
                amount_minor=price.amount_minor,
                currency=price.currency,
                display_price=price.amount_minor is not None,
                can_add_to_cart=True,
                can_checkout_online=True,
                action="ADD_TO_CART",
                action_label="Add to Cart",
            )

        return PricingDecision(
            mode=mode,
            amount_minor=None,
            currency=price.currency,
            display_price=False,
            can_add_to_cart=False,
            can_checkout_online=False,
            action="SIGN_IN",
            action_label="Sign In for Pricing",
        )

    if mode == PricingPolicyMode.NO_ONLINE_SALE:
        return PricingDecision(
            mode=mode,
            amount_minor=None,
            currency=price.currency,
            display_price=False,
            can_add_to_cart=False,
            can_checkout_online=False,
            action="REQUEST_QUOTE",
            action_label="Contact for Availability",
        )

    return PricingDecision(
        mode=PricingPolicyMode.NO_ONLINE_PRICE,
        amount_minor=None,
        currency=price.currency,
        display_price=False,
        can_add_to_cart=False,
        can_checkout_online=False,
        action="REQUEST_QUOTE",
        action_label="Request a Quote",
    )
