"""PT41 controlled catalog rollout: preserve historical IDs, never rename SKUs.

Run `plan` first. `apply` creates the 10 owner-confirmed SKU records, then
retires obsolete public listings without deleting any historical products,
variants, orders, quotes or prices. Database work is transactional.
"""

import argparse

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.catalog import Product, ProductLifecycleStatus
from app.services.catalog_seed import apply_catalog_manifest, load_catalog_manifest

# Immutable old identifiers are deliberately *not* repurposed into new SKUs.
LEGACY_SLUGS = {
    "DD15CAT-TTACPTV": "dd15cat-ttacptv",
    "DD15CAT-TTACRV": "dd15cat-ttacrv",
    "DD15CATPTV": "dd15catptv",
    "DD5ROAE": "dd5roae",
    "REFINE": "refine",
}


def retire_legacy_products(db: object) -> list[str]:
    """Deactivate superseded products after rejecting unsafe/unexpected state."""
    products = db.scalars(
        select(Product).where(Product.sku.in_(tuple(LEGACY_SLUGS)))
    ).all()
    changes: list[str] = []
    for product in products:
        if product.slug != LEGACY_SLUGS[product.sku]:
            raise RuntimeError(f"Legacy SKU/slug mismatch: {product.sku}")
        if product.online_sale_approved:
            raise RuntimeError(
                f"Legacy SKU {product.sku} is approved for online sales. "
                "Review sales and inventory obligations before retiring it."
            )
        if product.active or product.lifecycle_status != ProductLifecycleStatus.discontinued:
            product.active = False
            product.lifecycle_status = ProductLifecycleStatus.discontinued
            changes.append(product.sku)
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview/apply PT41 catalog transition")
    parser.add_argument("mode", choices=("plan", "apply"))
    args = parser.parse_args()
    catalog = load_catalog_manifest()
    expected = {
        "DD15SOFT", "DD20SOFT", "DD15CATRV", "DD20CATRV",
        "DD15CLEARPL1", "DD15CLEARPL2", "DD15CLEARPL3",
        "DD15CLEARPTV", "DD5RO", "DD6ROAE",
    }
    if {row["sku"] for row in catalog["products"]} != expected:
        raise RuntimeError("PT41 SKU list does not match the owner-confirmed 10-SKU set")

    settings = get_settings()
    engine = create_engine(settings.alembic_database_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with Session() as db:
        # Preflight retirement safety *before* creating catalog records.
        retired = retire_legacy_products(db)
        changes = apply_catalog_manifest(db, catalog)
        db.flush()
        print("Mode:", args.mode)
        print("Canonical products:", len(catalog["products"]))
        print("New products:", changes.products_created)
        print("Metadata updates:", changes.products_updated)
        print("New specifications:", changes.specifications_created)
        print("New images:", changes.images_created)
        print("Image metadata updates:", changes.images_updated)
        print("Superseded listings retired:", ", ".join(retired) if retired else "none")
        print("Historical SKUs retained unchanged; pricing and inventory untouched.")
        if args.mode == "apply":
            db.commit()
            print("APPLIED: catalog transaction committed")
        else:
            db.rollback()
            print("PLAN ONLY: transaction rolled back; no database changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
