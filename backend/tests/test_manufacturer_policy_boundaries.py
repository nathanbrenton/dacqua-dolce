import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.api.catalog import (
    pricing_read,
    public_document_reads,
)
from app.models.catalog import (
    PricingPolicyMode,
    ProductDocument,
    ProductDocumentType,
    ProductPrice,
)
from app.schemas.catalog import CatalogProductRead
from app.services import commerce


def public_price() -> ProductPrice:
    return ProductPrice(
        pricing_policy_mode=PricingPolicyMode.PUBLIC,
        amount_minor=12500,
        currency="USD",
        effective_from=(
            datetime.now(UTC)
            - timedelta(minutes=1)
        ),
        active=True,
    )


def test_unapproved_product_forces_no_online_sale() -> None:
    product = SimpleNamespace(
        prices=[public_price()],
        assisted_sale_required=False,
        online_sale_approved=False,
    )

    result = pricing_read(
        product,  # type: ignore[arg-type]
        authenticated=True,
    )

    assert result.mode == "NO_ONLINE_SALE"
    assert result.amount_minor is None
    assert result.display_price is False
    assert result.can_add_to_cart is False
    assert result.can_checkout_online is False
    assert result.action == "REQUEST_QUOTE"


def test_assisted_sale_product_forces_request_quote() -> None:
    product = SimpleNamespace(
        prices=[public_price()],
        assisted_sale_required=True,
        online_sale_approved=True,
    )

    result = pricing_read(
        product,  # type: ignore[arg-type]
        authenticated=True,
    )

    assert result.mode == "NO_ONLINE_SALE"
    assert result.can_add_to_cart is False
    assert result.can_checkout_online is False
    assert result.action == "REQUEST_QUOTE"
    assert result.action_label == "Request a Quote"


def test_public_catalog_schema_hides_manufacturer() -> None:
    assert (
        "manufacturer"
        not in CatalogProductRead.model_fields
    )


def test_documents_require_explicit_public_approval() -> None:
    approved = ProductDocument(
        title="Approved guide",
        document_type=(
            ProductDocumentType.care_guide
        ),
        storage_path="/docs/approved.pdf",
        content_type="application/pdf",
        version="1",
        public=True,
        active=True,
    )

    private = ProductDocument(
        title="Internal manufacturer document",
        document_type=(
            ProductDocumentType.specification
        ),
        storage_path="/docs/internal.pdf",
        content_type="application/pdf",
        version="1",
        public=False,
        active=True,
    )

    inactive = ProductDocument(
        title="Retired guide",
        document_type=(
            ProductDocumentType.care_guide
        ),
        storage_path="/docs/retired.pdf",
        content_type="application/pdf",
        version="1",
        public=True,
        active=False,
    )

    result = public_document_reads(
        [
            approved,
            private,
            inactive,
        ]
    )

    assert len(result) == 1
    assert result[0].title == "Approved guide"


class ProductOnlyDatabase:
    def __init__(
        self,
        *,
        online_sale_approved: bool = False,
        assisted_sale_required: bool = False,
    ) -> None:
        self.calls = 0
        self.online_sale_approved = online_sale_approved
        self.assisted_sale_required = assisted_sale_required

    def scalar(
        self,
        statement: object,
    ) -> object:
        self.calls += 1

        return SimpleNamespace(
            id=uuid.uuid4(),
            online_sale_approved=self.online_sale_approved,
            assisted_sale_required=self.assisted_sale_required,
        )


def test_cart_service_rechecks_online_sale_policy() -> None:
    database = ProductOnlyDatabase()

    with pytest.raises(
        commerce.CommerceError,
        match="not approved for online sale",
    ):
        commerce.add_item_to_cart(
            database,  # type: ignore[arg-type]
            user_id=uuid.uuid4(),
            product_id=uuid.uuid4(),
            variant_id=None,
            quantity=1,
        )

    assert database.calls == 1


def test_cart_service_rechecks_assisted_sale_requirement() -> None:
    database = ProductOnlyDatabase(
        online_sale_approved=True,
        assisted_sale_required=True,
    )

    with pytest.raises(
        commerce.CommerceError,
        match="requires employee review",
    ):
        commerce.add_item_to_cart(
            database,  # type: ignore[arg-type]
            user_id=uuid.uuid4(),
            product_id=uuid.uuid4(),
            variant_id=None,
            quantity=1,
        )

    assert database.calls == 1
