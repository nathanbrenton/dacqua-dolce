import uuid
from types import SimpleNamespace

import pytest

from app.models.quote import CommercialChargeKind, FormalQuoteStatus
from app.services import tax_automation


class ScalarRows:
    def __init__(self, rows: list[object]) -> None:
        self.rows = rows

    def all(self) -> list[object]:
        return self.rows


class ClassificationDatabase:
    def __init__(self, rows: list[object]) -> None:
        self.rows = rows

    def scalars(self, _statement: object) -> ScalarRows:
        return ScalarRows(self.rows)


def draft_quote(
    *,
    items: list[object],
    charges: list[object] | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        status=FormalQuoteStatus.draft,
        currency="USD",
        delivery_address_snapshot={
            "line1": "123 Main St",
            "city": "Irvine",
            "region_code": "CA",
            "postal_code": "92614",
            "country_code": "US",
        },
        items=items,
        charges=charges or [],
    )


def test_tax_request_allows_multiple_lines_for_same_product() -> None:
    product_id = uuid.uuid4()
    classification = SimpleNamespace(
        product_id=product_id,
        tax_code="txcd_reviewed",
    )
    quote = draft_quote(
        items=[
            SimpleNamespace(
                product_id=product_id,
                sku_snapshot="SKU-A",
                line_total_minor=10000,
                quantity=1,
            ),
            SimpleNamespace(
                product_id=product_id,
                sku_snapshot="SKU-A-SECOND-LINE",
                line_total_minor=5000,
                quantity=1,
            ),
        ]
    )

    request = tax_automation._request_from_quote(
        ClassificationDatabase([classification]),  # type: ignore[arg-type]
        formal_quote=quote,  # type: ignore[arg-type]
    )

    assert len(request.line_items) == 2
    assert sum(item.amount_minor for item in request.line_items) == 15000
    assert request.line_items[0].tax_code == "txcd_reviewed"
    assert request.idempotency_key is not None


def test_tax_request_blocks_unmapped_commercial_adjustment() -> None:
    product_id = uuid.uuid4()
    classification = SimpleNamespace(
        product_id=product_id,
        tax_code="txcd_reviewed",
    )
    quote = draft_quote(
        items=[
            SimpleNamespace(
                product_id=product_id,
                sku_snapshot="SKU-A",
                line_total_minor=10000,
                quantity=1,
            )
        ],
        charges=[
            SimpleNamespace(
                kind=CommercialChargeKind.shipping_insurance.value,
                amount_minor=300,
            )
        ],
    )

    with pytest.raises(tax_automation.TaxAutomationError, match="shipping_insurance"):
        tax_automation._request_from_quote(
            ClassificationDatabase([classification]),  # type: ignore[arg-type]
            formal_quote=quote,  # type: ignore[arg-type]
        )


def test_tax_request_requires_explicit_product_classification() -> None:
    product_id = uuid.uuid4()
    quote = draft_quote(
        items=[
            SimpleNamespace(
                product_id=product_id,
                sku_snapshot="SKU-A",
                line_total_minor=10000,
                quantity=1,
            )
        ]
    )

    with pytest.raises(tax_automation.TaxAutomationError, match="SKU-A"):
        tax_automation._request_from_quote(
            ClassificationDatabase([]),  # type: ignore[arg-type]
            formal_quote=quote,  # type: ignore[arg-type]
        )
