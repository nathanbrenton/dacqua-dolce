import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.catalog import (
    InventoryStatus,
    Product,
    ProductInventory,
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

CART_RESERVATION_TTL = timedelta(
    minutes=30,
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


def active_reserved_quantity(
    db: Session,
    *,
    product_id: uuid.UUID,
    variant_id: uuid.UUID | None,
    now: datetime | None = None,
) -> int:
    effective_now = (
        now
        if now is not None
        else datetime.now(UTC)
    )

    statement = (
        select(
            func.coalesce(
                func.sum(CartItem.quantity),
                0,
            )
        )
        .join(
            Cart,
            Cart.id == CartItem.cart_id,
        )
        .where(
            Cart.status == CartStatus.active,
            CartItem.product_id == product_id,
            CartItem.reservation_expires_at.is_not(
                None
            ),
            CartItem.reservation_expires_at
            > effective_now,
        )
    )

    if variant_id is not None:
        statement = statement.where(
            CartItem.variant_id == variant_id
        )

    return int(
        db.scalar(statement)
        or 0
    )


def _inventory_for_cart_item(
    db: Session,
    *,
    product_id: uuid.UUID,
    variant_id: uuid.UUID | None,
) -> ProductInventory | None:
    def load(
        scope_variant_id: uuid.UUID | None,
    ) -> ProductInventory | None:
        statement = select(
            ProductInventory
        ).where(
            ProductInventory.product_id
            == product_id,
        )

        if scope_variant_id is None:
            statement = statement.where(
                ProductInventory.variant_id.is_(
                    None
                )
            )
        else:
            statement = statement.where(
                ProductInventory.variant_id
                == scope_variant_id
            )

        return db.scalar(
            statement
            .order_by(
                ProductInventory.updated_at.desc()
            )
            .with_for_update()
        )

    if variant_id is not None:
        variant_inventory = load(
            variant_id
        )

        if variant_inventory is not None:
            return variant_inventory

    return load(None)


def _reserve_quantity(
    db: Session,
    *,
    item: CartItem,
    inventory: ProductInventory | None,
    desired_quantity: int,
    now: datetime,
) -> None:
    if (
        inventory is None
        or inventory.inventory_status
        == InventoryStatus.not_tracked
    ):
        item.reservation_expires_at = None
        return

    if (
        inventory.inventory_status
        == InventoryStatus.unavailable
    ):
        raise CommerceError(
            "This system is currently unavailable."
        )

    reserved_quantity = (
        active_reserved_quantity(
            db,
            product_id=inventory.product_id,
            variant_id=inventory.variant_id,
            now=now,
        )
    )

    current_item_reserved = 0

    if (
        item.reservation_expires_at
        is not None
        and item.reservation_expires_at > now
    ):
        current_item_reserved = item.quantity

    available_for_item = (
        inventory.quantity_on_hand
        - reserved_quantity
        + current_item_reserved
    )

    if desired_quantity > available_for_item:
        raise CommerceError(
            "The requested quantity is not "
            "currently available."
        )

    item.reservation_expires_at = (
        now + CART_RESERVATION_TTL
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
        raise CommerceError(
            "System not found."
        )

    if variant_id is not None:
        variant = db.scalar(
            select(ProductVariant).where(
                ProductVariant.id == variant_id,
                ProductVariant.product_id
                == product.id,
                ProductVariant.active.is_(True),
            )
        )

        if variant is None:
            raise CommerceError(
                "System variant not found."
            )

    price = _selected_price(
        product,
        variant_id=variant_id,
    )

    decision = resolve_pricing(
        price,
        authenticated=True,
    )

    if (
        price is None
        or not decision.can_add_to_cart
        or price.amount_minor is None
    ):
        raise CommerceError(
            "This system is not available "
            "for online cart purchase."
        )

    cart = get_or_create_active_cart(
        db,
        user_id=user_id,
    )

    existing = db.scalar(
        select(CartItem)
        .where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product.id,
            (
                CartItem.variant_id == variant_id
                if variant_id is not None
                else CartItem.variant_id.is_(
                    None
                )
            ),
        )
        .with_for_update()
    )

    inventory = _inventory_for_cart_item(
        db,
        product_id=product.id,
        variant_id=variant_id,
    )

    now = datetime.now(UTC)

    if existing is not None:
        desired_quantity = (
            existing.quantity + quantity
        )

        _reserve_quantity(
            db,
            item=existing,
            inventory=inventory,
            desired_quantity=desired_quantity,
            now=now,
        )

        existing.quantity = desired_quantity
        existing.unit_amount_minor = (
            price.amount_minor
        )
        existing.currency = price.currency
        existing.pricing_policy_mode = (
            price.pricing_policy_mode
        )

        db.flush()

        return existing

    item = CartItem(
        cart_id=cart.id,
        product_id=product.id,
        variant_id=variant_id,
        quantity=quantity,
        unit_amount_minor=price.amount_minor,
        currency=price.currency,
        pricing_policy_mode=(
            price.pricing_policy_mode
        ),
    )

    _reserve_quantity(
        db,
        item=item,
        inventory=inventory,
        desired_quantity=quantity,
        now=now,
    )

    db.add(item)
    db.flush()

    return item
