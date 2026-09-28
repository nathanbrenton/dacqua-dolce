import pytest
from pydantic import ValidationError

from app.models.catalog import (
    InventoryStatus,
    PricingPolicyMode,
    ProductRelationshipType,
)
from app.schemas.operations import (
    InventoryUpdateRequest,
    OperationsInventoryRead,
    OperationsPricingRead,
    OperationsProductRead,
    OperationsProductRelationshipRead,
    PricingUpdateRequest,
    ProductRelationshipCreateRequest,
    ProductRelationshipUpdateRequest,
    QuoteNotesUpdate,
)


@pytest.mark.parametrize(
    "mode",
    [
        PricingPolicyMode.PUBLIC,
        PricingPolicyMode.MAP_LIMITED,
        PricingPolicyMode.CART_ONLY,
        PricingPolicyMode.LOGIN_REQUIRED,
    ],
)
def test_price_amount_required_for_online_purchase_modes(
    mode: PricingPolicyMode,
) -> None:
    with pytest.raises(ValidationError):
        PricingUpdateRequest(
            mode=mode,
            amount_minor=None,
            currency="USD",
        )


@pytest.mark.parametrize(
    "mode",
    [
        PricingPolicyMode.PRIVATE_QUOTE,
        PricingPolicyMode.NO_ONLINE_PRICE,
        PricingPolicyMode.NO_ONLINE_SALE,
    ],
)
def test_restricted_modes_reject_online_amount(
    mode: PricingPolicyMode,
) -> None:
    with pytest.raises(ValidationError):
        PricingUpdateRequest(
            mode=mode,
            amount_minor=10000,
            currency="USD",
        )


def test_currency_is_normalized() -> None:
    payload = PricingUpdateRequest(
        mode=PricingPolicyMode.PUBLIC,
        amount_minor=10000,
        currency="usd",
    )

    assert payload.currency == "USD"


def test_inventory_reserved_is_not_operator_editable() -> None:
    with pytest.raises(ValidationError):
        InventoryUpdateRequest(
            status=InventoryStatus.in_stock,
            quantity_on_hand=1,
            quantity_reserved=1,
        )

def test_quote_notes_are_trimmed() -> None:
    payload = QuoteNotesUpdate(
        internal_notes="  Called customer; awaiting reply.  ",
    )

    assert payload.internal_notes == (
        "Called customer; awaiting reply."
    )


def test_blank_quote_notes_become_none() -> None:
    payload = QuoteNotesUpdate(
        internal_notes="   ",
    )

    assert payload.internal_notes is None


def test_quote_notes_have_reasonable_limit() -> None:
    with pytest.raises(ValidationError):
        QuoteNotesUpdate(
            internal_notes="x" * 8001,
        )


def test_operations_product_exposes_catalog_architecture_context() -> None:
    product = OperationsProductRead(
        id="00000000-0000-0000-0000-000000000001",
        sku="DD-TEST",
        name="Test System",
        category="Water treatment",
        manufacturer="D'Acqua Dolce",
        product_family="Harmony",
        system_type="Water Conditioner",
        active_variant_count=2,
        public_option_count=0,
        active=True,
        online_sale_approved=False,
        pricing=OperationsPricingRead(
            mode="NO_ONLINE_SALE",
            amount_minor=None,
            currency=None,
            effective_from=None,
        ),
        inventory=OperationsInventoryRead(
            status="not_tracked",
            quantity_on_hand=0,
            quantity_reserved=0,
        ),
    )

    assert product.product_family == "Harmony"
    assert product.system_type == "Water Conditioner"
    assert product.active_variant_count == 2
    assert product.public_option_count == 0


def test_product_relationship_create_defaults_internal() -> None:
    payload = ProductRelationshipCreateRequest(
        related_product_id="00000000-0000-0000-0000-000000000002",
        relationship_type=ProductRelationshipType.option,
    )

    assert payload.public is False
    assert payload.active is True
    assert payload.sort_order == 0


def test_product_relationship_update_requires_explicit_visibility() -> None:
    with pytest.raises(ValidationError):
        ProductRelationshipUpdateRequest(
            relationship_type=ProductRelationshipType.accessory,
            active=True,
            sort_order=0,
        )


def test_operations_product_relationship_is_structured() -> None:
    relationship = OperationsProductRelationshipRead(
        id="00000000-0000-0000-0000-000000000003",
        related_product_id="00000000-0000-0000-0000-000000000002",
        related_sku="DD-UV",
        related_name="UV Option",
        relationship_type=ProductRelationshipType.option,
        public=False,
        active=True,
        sort_order=0,
    )

    assert relationship.relationship_type == ProductRelationshipType.option
    assert relationship.public is False
