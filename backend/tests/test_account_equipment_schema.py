import uuid

from app.schemas.account import CustomerEquipmentRead
from app.schemas.operations import CustomerEquipmentCreateRequest, CustomerEquipmentUpdateRequest


def test_customer_equipment_read_accepts_public_document_metadata():
    payload = CustomerEquipmentRead(
        id="equipment-1",
        product_id="product-1",
        product_name="Harmony",
        product_family="Harmony",
        system_type="Water Conditioner",
        sku="DD15CAT-TTACPTV",
        documents=[{
            "title": "Care guide",
            "document_type": "care_guide",
            "path": "/docs/care.pdf",
            "content_type": "application/pdf",
            "version": "1",
        }],
    )
    assert payload.documents[0].document_type == "care_guide"


def test_equipment_create_cleans_optional_text():
    payload = CustomerEquipmentCreateRequest(
        product_id=uuid.uuid4(),
        serial_number="  ABC123  ",
        location_label="  Garage  ",
    )
    assert payload.serial_number == "ABC123"
    assert payload.location_label == "Garage"


def test_equipment_update_can_deactivate_record():
    payload = CustomerEquipmentUpdateRequest(active=False)
    assert payload.active is False
