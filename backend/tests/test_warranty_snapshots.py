from datetime import UTC, datetime
from types import SimpleNamespace

from app.models.catalog import ProductDocumentType
from app.services.warranties import warranty_document_is_sale_ready


def warranty_document(**overrides):
    values = {
        "document_type": ProductDocumentType.warranty,
        "active": True,
        "public": True,
        "verified_at": datetime(2026, 10, 1, tzinfo=UTC),
        "checksum_sha256": "a" * 64,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_sale_ready_warranty_requires_verification_and_checksum() -> None:
    assert warranty_document_is_sale_ready(warranty_document()) is True
    assert warranty_document_is_sale_ready(
        warranty_document(verified_at=None)
    ) is False
    assert warranty_document_is_sale_ready(
        warranty_document(checksum_sha256=None)
    ) is False
    assert warranty_document_is_sale_ready(
        warranty_document(checksum_sha256="not-a-sha256")
    ) is False


def test_nonpublic_or_inactive_warranty_is_not_sale_ready() -> None:
    assert warranty_document_is_sale_ready(
        warranty_document(public=False)
    ) is False
    assert warranty_document_is_sale_ready(
        warranty_document(active=False)
    ) is False


def test_non_warranty_document_is_not_warranty_ready() -> None:
    document = warranty_document(document_type=ProductDocumentType.owners_manual)
    assert warranty_document_is_sale_ready(document) is False
