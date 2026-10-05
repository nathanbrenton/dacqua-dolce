from datetime import UTC, datetime
from types import SimpleNamespace

from app.api.catalog import public_document_reads
from app.models.catalog import ProductDocumentType


def warranty_document(**overrides):
    values = {
        "title": "Manufacturer Warranty",
        "document_type": ProductDocumentType.warranty,
        "storage_path": "/documents/warranty.pdf",
        "content_type": "application/pdf",
        "version": "1",
        "verified_at": datetime(2026, 10, 1, tzinfo=UTC),
        "checksum_sha256": "a" * 64,
        "active": True,
        "public": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_public_warranty_uses_sale_ready_checksum_boundary() -> None:
    result = public_document_reads(
        [
            warranty_document(),
            warranty_document(
                title="Invalid checksum",
                checksum_sha256="g" * 64,
            ),
        ]
    )

    assert [document.title for document in result] == ["Manufacturer Warranty"]
