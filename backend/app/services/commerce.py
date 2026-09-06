import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.catalog import (
    Product,
    ProductPrice,
    ProductVariant,
)
from app.models.commerce import (
    Cart,
    CartItem,
    CartStatus,
)
from app.services.pricing import (
    resolve_pricing,
    select_effective_price,
)


class CommerceError(ValueError):
    pass


def get_or_create_active_cart(
    db: Session,
    *,
    user_id: uuid.UUID,
) -> Cart:
    cart = db.scalar(
        select(Cart)
        .where(
            Cart.user_id == user_id,
            Cart.status == CartStatus.active,
        )
        .order_by(Cart.created_at.desc())
    )

    if cart is None:
        cart = Cart(
            user_id=user_id,
            status=CartStatus.active,
        )
        db.add(cart)
        db.flush()

    return cart


def _selected_price(
    product: Product,
    *,
    variant_id: uuid.UUID | None,
) -> ProductPrice | None:
    if variant_id is not None:
        variant_price = select_effective_price(
            product.prices,
            variant_id=variant_id,
        )

        if variant_price is not None:
            return variant_price

    return select_effective_price(
        product.prices,
        variant_id=None,
    )


def add_item_to_cart(
    db: Session,
    *,
    user_id: uuid.UUID,
    product_id: uuid.UUID,
    variant_id: uuid.UUID | None,
    quantity: int,
) -> CartItem:
    product = db.scalar(
        select(Product).where(
            Product.id == product_id,
            Product.active.is_(True),
        )
    )

    if product is None:
        raise CommerceError("System not found.")

    if variant_id is not None:
        variant = db.scalar(
            select(ProductVariant).where(
                ProductVariant.id == variant_id,
                ProductVariant.product_id == product.id,
                ProductVariant.active.is_(True),
            )
        )

        if variant is None:
            raise CommerceError("System variant not found.")

    price = _selected_price(
        product,
        variant_id=variant_id,
    )

    decision = resolve_pricing(
        price,
        authenticated=True,
    )

    if price is None or not decision.can_add_to_cart or price.amount_minor is None:
        raise CommerceError("This system is not available for online cart purchase.")

    cart = get_or_create_active_cart(
        db,
        user_id=user_id,
    )

    existing = db.scalar(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product.id,
            (
                CartItem.variant_id == variant_id
                if variant_id is not None
                else CartItem.variant_id.is_(None)
            ),
        )
    )

    if existing is not None:
        existing.quantity += quantity
        existing.unit_amount_minor = price.amount_minor
        existing.currency = price.currency
        existing.pricing_policy_mode = price.pricing_policy_mode
        db.flush()

        return existing

    item = CartItem(
        cart_id=cart.id,
        product_id=product.id,
        variant_id=variant_id,
        quantity=quantity,
        unit_amount_minor=price.amount_minor,
        currency=price.currency,
        pricing_policy_mode=(price.pricing_policy_mode),
    )

    db.add(item)
    db.flush()

    return item
