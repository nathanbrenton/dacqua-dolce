from app.models.catalog import ProductDocumentType
from app.schemas.catalog import StockNotificationRequest


def test_stock_notification_email_is_normalized() -> None:
    payload = StockNotificationRequest(
        email="  Customer@Example.Test  ",
    )

    assert payload.email == "customer@example.test"


def test_requested_customer_document_types_are_representable() -> None:
    assert ProductDocumentType.specification.value == "specification"
    assert ProductDocumentType.owners_manual.value == "owners_manual"
    assert ProductDocumentType.installation.value == "installation"
    assert ProductDocumentType.maintenance_guide.value == "maintenance_guide"
    assert ProductDocumentType.warranty.value == "warranty"
    assert ProductDocumentType.service_schedule.value == "service_schedule"
    assert ProductDocumentType.water_test_report.value == "water_test_report"
