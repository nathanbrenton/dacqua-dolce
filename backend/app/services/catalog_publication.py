"""Public catalog publication rules for product lifecycle retirement."""

from datetime import UTC, datetime
from typing import Protocol


class PublicCatalogProduct(Protocol):
    active: bool
    public_retire_at: datetime | None


def product_is_publicly_visible(
    product: PublicCatalogProduct,
    *,
    now: datetime | None = None,
) -> bool:
    """Return whether a product may appear on customer-facing catalog routes."""

    if not product.active:
        return False

    retire_at = product.public_retire_at
    if retire_at is None:
        return True

    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        raise ValueError("Public-catalog comparison time must be timezone-aware.")

    if retire_at.tzinfo is None:
        raise ValueError("Product public retirement timestamp must be timezone-aware.")

    return retire_at > current
