import pytest
from pydantic import ValidationError

from app.models.catalog import (
    InventoryStatus,
    PricingPolicyMode,
    ProductRelationshipType,
)
from app.models.commerce import FulfillmentStatus
from app.schemas.operations import (
    InventoryUpdateRequest,
    OperationsInventoryRead,
    OperationsPricingRead,
    OperationsProductRead,
    OperationsProductRelationshipRead,
    OperationsSummaryRead,
    OrderFulfillmentUpdate,
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


def test_operations_summary_exposes_recommendation_triage_counts() -> None:
    summary = OperationsSummaryRead(
        new_quotes=3,
        open_quotes=5,
        recommendation_human_review=2,
        recommendation_lab_testing=1,
        active_products=4,
        failed_email_deliveries=0,
    )

    assert summary.recommendation_human_review == 2
    assert summary.recommendation_lab_testing == 1

def test_inventory_lead_time_is_trimmed() -> None:
    payload = InventoryUpdateRequest(
        status=InventoryStatus.backordered,
        quantity_on_hand=0,
        estimated_lead_time="  2–3 weeks  ",
    )

    assert payload.estimated_lead_time == "2–3 weeks"


def test_blank_inventory_lead_time_becomes_none() -> None:
    payload = InventoryUpdateRequest(
        status=InventoryStatus.unavailable,
        quantity_on_hand=0,
        estimated_lead_time="   ",
    )

    assert payload.estimated_lead_time is None


def test_fulfillment_update_strips_optional_text() -> None:
    payload = OrderFulfillmentUpdate(
        status=FulfillmentStatus.supplier_ordered,
        supplier_order_reference="  PO-12345  ",
    )

    assert payload.supplier_order_reference == "PO-12345"


def test_fulfillment_update_forbids_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        OrderFulfillmentUpdate(
            status=FulfillmentStatus.received_ready,
            internal_note="not part of fulfillment contract",
        )


def test_product_relationship_consumable_interval_requires_consumable_flag() -> None:
    with pytest.raises(ValidationError):
        ProductRelationshipCreateRequest(
            related_product_id="00000000-0000-0000-0000-000000000001",
            relationship_type=ProductRelationshipType.accessory,
            public=True,
            active=True,
            is_consumable=False,
            replacement_interval_days=180,
            sort_order=0,
        )


def test_product_relationship_consumable_interval_is_optional() -> None:
    payload = ProductRelationshipCreateRequest(
        related_product_id="00000000-0000-0000-0000-000000000001",
        relationship_type=ProductRelationshipType.accessory,
        public=True,
        active=True,
        is_consumable=True,
        replacement_interval_days=None,
        sort_order=0,
    )

    assert payload.is_consumable is True
    assert payload.replacement_interval_days is None
