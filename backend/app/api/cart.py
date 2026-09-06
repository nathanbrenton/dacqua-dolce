import uuid

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)
from sqlalchemy import select

from app.api.dependencies.auth import (
    CurrentUser,
    DatabaseSession,
)
from app.models.catalog import Product
from app.models.commerce import (
    CartItem,
)
from app.schemas.commerce import (
    CartItemCreate,
    CartItemRead,
    CartRead,
)
from app.services.audit import (
    record_audit_event,
)
from app.services.commerce import (
    CommerceError,
    add_item_to_cart,
    get_or_create_active_cart,
)

router = APIRouter(
    prefix="/cart",
    tags=["cart"],
)


def cart_read(
    db: DatabaseSession,
    *,
    user_id: uuid.UUID,
) -> CartRead:
    cart = get_or_create_active_cart(
        db,
        user_id=user_id,
    )

    rows = db.execute(
        select(
            CartItem,
            Product,
        )
        .join(
            Product,
            Product.id == CartItem.product_id,
        )
        .where(CartItem.cart_id == cart.id)
        .order_by(CartItem.created_at)
    ).all()

    items = [
        CartItemRead(
            id=str(item.id),
            product_id=str(item.product_id),
            variant_id=(str(item.variant_id) if item.variant_id is not None else None),
            sku=product.sku,
            name=product.name,
            quantity=item.quantity,
            unit_amount_minor=(item.unit_amount_minor),
            line_total_minor=(item.unit_amount_minor * item.quantity),
            currency=item.currency,
        )
        for item, product in rows
    ]

    currencies = {item.currency for item in items}

    currency = next(iter(currencies)) if len(currencies) == 1 else None

    return CartRead(
        id=str(cart.id),
        status=cart.status.value,
        items=items,
        total_amount_minor=sum(item.line_total_minor for item in items),
        currency=currency,
    )


@router.get(
    "",
    response_model=CartRead,
)
def get_cart(
    db: DatabaseSession,
    current_user: CurrentUser,
) -> CartRead:
    result = cart_read(
        db,
        user_id=current_user.id,
    )

    db.commit()

    return result


@router.post(
    "/items",
    response_model=CartRead,
    status_code=status.HTTP_201_CREATED,
)
def add_cart_item(
    payload: CartItemCreate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> CartRead:
    try:
        product_id = uuid.UUID(payload.product_id)
        variant_id = uuid.UUID(payload.variant_id) if payload.variant_id is not None else None
    except ValueError as exc:
        raise HTTPException(
            status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
            detail="Invalid product identifier.",
        ) from exc

    try:
        item = add_item_to_cart(
            db,
            user_id=current_user.id,
            product_id=product_id,
            variant_id=variant_id,
            quantity=payload.quantity,
        )
    except CommerceError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    record_audit_event(
        db,
        action="cart.item_added",
        entity_type="cart_item",
        entity_id=str(item.id),
        actor_user_id=current_user.id,
        metadata={
            "product_id": str(product_id),
            "quantity": payload.quantity,
        },
    )

    db.commit()

    return cart_read(
        db,
        user_id=current_user.id,
    )


@router.delete(
    "/items/{item_id}",
    response_model=CartRead,
)
def remove_cart_item(
    item_id: uuid.UUID,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> CartRead:
    cart = get_or_create_active_cart(
        db,
        user_id=current_user.id,
    )

    item = db.scalar(
        select(CartItem).where(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id,
        )
    )

    if item is None:
        raise HTTPException(
            status_code=(status.HTTP_404_NOT_FOUND),
            detail="Cart item not found.",
        )

    record_audit_event(
        db,
        action="cart.item_removed",
        entity_type="cart_item",
        entity_id=str(item.id),
        actor_user_id=current_user.id,
    )

    db.delete(item)
    db.commit()

    return cart_read(
        db,
        user_id=current_user.id,
    )
