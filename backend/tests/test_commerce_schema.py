import pytest
from pydantic import ValidationError

from app.schemas.commerce import (
    CartItemCreate,
)


def test_cart_quantity_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        CartItemCreate(
            product_id="abc",
            quantity=0,
        )


def test_cart_quantity_has_reasonable_cap() -> None:
    with pytest.raises(ValidationError):
        CartItemCreate(
            product_id="abc",
            quantity=100,
        )
