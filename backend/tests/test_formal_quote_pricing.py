import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException

from app.models.catalog import (
    PricingPolicyMode,
    Product,
    ProductPrice,
)
from app.services.formal_quotes import (
    FormalQuoteLineInput,
    _line_snapshot,
)


class ScalarRows:
    def __init__(self, rows: list[object]) -> None:
        self.rows = rows

    def all(self) -> list[object]:
        return self.rows


class FakeDatabase:
    def __init__(self, product: Product, prices: list[ProductPrice]) -> None:
        self.product = product
        self.prices = prices

    def get(self, model: object, identifier: object) -> object | None:
        if model is Product and identifier == self.product.id:
            return self.product
        return None

    def scalars(self, statement: object) -> ScalarRows:
        return ScalarRows(list(self.prices))

    def scalar(self, statement: object) -> None:
        return None


def product_and_price(
    mode: PricingPolicyMode,
    amount_minor: int | None,
) -> tuple[Product, ProductPrice]:
    product_id = uuid.uuid4()
    product = Product(
        id=product_id,
        manufacturer_id=uuid.uuid4(),
        category_id=uuid.uuid4(),
        name="Origin",
        slug="origin",
        sku="ORIGIN",
        description="Test product",
        public_path="/products/origin",
        active=True,
        online_sale_approved=False,
    )
    price = ProductPrice(
        product_id=product_id,
        variant_id=None,
        pricing_policy_mode=mode,
        amount_minor=amount_minor,
        currency="USD",
        effective_from=datetime.now(UTC) - timedelta(minutes=1),
        active=True,
    )
    return product, price


def test_catalog_amount_is_used_when_quote_price_is_blank() -> None:
    product, price = product_and_price(PricingPolicyMode.PUBLIC, 125000)
    db = FakeDatabase(product, [price])

    item, currency = _line_snapshot(
        db,  # type: ignore[arg-type]
        line=FormalQuoteLineInput(
            product_id=product.id,
            variant_id=None,
            quantity=2,
            unit_amount_minor=None,
        ),
        allow_catalog_price_override=False,
    )

    assert currency == "USD"
    assert item.unit_amount_minor == 125000
    assert item.line_total_minor == 250000
    assert item.pricing_policy_mode_snapshot == "PUBLIC"


def test_employee_cannot_override_authoritative_catalog_amount() -> None:
    product, price = product_and_price(PricingPolicyMode.PUBLIC, 125000)
    db = FakeDatabase(product, [price])

    with pytest.raises(HTTPException) as exc:
        _line_snapshot(
            db,  # type: ignore[arg-type]
            line=FormalQuoteLineInput(
                product_id=product.id,
                variant_id=None,
                quantity=1,
                unit_amount_minor=120000,
            ),
            allow_catalog_price_override=False,
        )

    assert exc.value.status_code == 403


def test_private_quote_accepts_employee_entered_amount() -> None:
    product, price = product_and_price(PricingPolicyMode.PRIVATE_QUOTE, None)
    db = FakeDatabase(product, [price])

    item, _ = _line_snapshot(
        db,  # type: ignore[arg-type]
        line=FormalQuoteLineInput(
            product_id=product.id,
            variant_id=None,
            quantity=1,
            unit_amount_minor=149900,
        ),
        allow_catalog_price_override=False,
    )

    assert item.unit_amount_minor == 149900
    assert item.pricing_policy_mode_snapshot == "PRIVATE_QUOTE"
