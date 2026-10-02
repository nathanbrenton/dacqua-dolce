from __future__ import annotations

import string

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.catalog import Product, ProductDocument, ProductDocumentType
from app.models.quote import FormalQuote, FormalQuoteWarrantySnapshot

_HEX = frozenset(string.hexdigits)


def warranty_document_is_sale_ready(document: ProductDocument) -> bool:
    checksum = (document.checksum_sha256 or "").strip()
    return (
        document.document_type == ProductDocumentType.warranty
        and document.active
        and document.public
        and document.verified_at is not None
        and len(checksum) == 64
        and all(character in _HEX for character in checksum)
    )


def snapshot_quote_warranties(
    db: Session,
    *,
    formal_quote: FormalQuote,
) -> list[FormalQuoteWarrantySnapshot]:
    existing = list(getattr(formal_quote, "warranty_snapshots", []))
    if existing:
        return existing

    snapshots: list[FormalQuoteWarrantySnapshot] = []
    sort_order = 0

    for item in formal_quote.items:
        if item.product_id is None:
            continue

        product = db.get(Product, item.product_id)
        if product is None:
            continue

        documents = db.scalars(
            select(ProductDocument)
            .where(
                ProductDocument.product_id == product.id,
                ProductDocument.document_type == ProductDocumentType.warranty,
                ProductDocument.active.is_(True),
                ProductDocument.public.is_(True),
            )
            .order_by(ProductDocument.created_at, ProductDocument.id)
        ).all()

        for document in documents:
            if not warranty_document_is_sale_ready(document):
                continue

            snapshot = FormalQuoteWarrantySnapshot(
                formal_quote_id=formal_quote.id,
                formal_quote_item_id=item.id,
                product_document_id=document.id,
                product_id_snapshot=product.id,
                sku_snapshot=item.sku_snapshot,
                product_name_snapshot=item.name_snapshot,
                manufacturer_name_snapshot=product.manufacturer.name,
                title_snapshot=document.title,
                version_snapshot=document.version,
                storage_path_snapshot=document.storage_path,
                content_type_snapshot=document.content_type,
                checksum_sha256_snapshot=document.checksum_sha256,
                source_reference_snapshot=document.source_reference,
                verified_at_snapshot=document.verified_at,
                sort_order=sort_order,
            )
            db.add(snapshot)
            snapshots.append(snapshot)
            sort_order += 1

    db.flush()
    formal_quote.warranty_snapshots = snapshots
    return snapshots
