"""Idempotently seed the initial D'Acqua Dolce catalog from owner-supplied SKU sheets.

This seed intentionally contains no prices and no health/performance claims.
Pricing therefore resolves conservatively through the application's
NO_ONLINE_PRICE behavior until authoritative business pricing is loaded.
"""

from dataclasses import dataclass

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.catalog import (
    Manufacturer,
    Product,
    ProductCategory,
    ProductImage,
)


@dataclass(frozen=True)
class SeedImage:
    path: str
    alt_text: str
    sort_order: int


@dataclass(frozen=True)
class SeedProduct:
    sku: str
    name: str
    slug: str
    description: str
    product_family: str
    category_slug: str
    images: tuple[SeedImage, ...]


PRODUCTS = (
    SeedProduct(
        sku="DD15CATPTV",
        name="1.5cf Catalytic Carbon Filter — Pass-through Valve",
        slug="dd15catptv",
        description=(
            "1.5 cubic foot catalytic carbon filter configured "
            "with a pass-through valve."
        ),
        product_family="Catalytic Carbon Filter",
        category_slug="whole-home-filtration",
        images=(
            SeedImage(
                path=(
                    "/products/media/"
                    "1-5cf-pass-through-valve-dimensions.webp"
                ),
                alt_text=(
                    "D'Acqua Dolce 1.5 cubic foot filtration tank "
                    "with pass-through valve and dimensions"
                ),
                sort_order=0,
            ),
            SeedImage(
                path=(
                    "/products/media/"
                    "dd15catptv-spec-dimensions.webp"
                ),
                alt_text=(
                    "DD15CATPTV 1.5cf Catalytic Carbon Filter "
                    "with Pass-through Valve specification dimensions"
                ),
                sort_order=10,
            ),
        ),
    ),
    SeedProduct(
        sku="DD15CATRV",
        name="1.5cf Catalytic Carbon Filter — Regenerating Valve",
        slug="dd15catrv",
        description=(
            "1.5 cubic foot catalytic carbon filter configured "
            "with a regenerating valve."
        ),
        product_family="Catalytic Carbon Filter",
        category_slug="whole-home-filtration",
        images=(
            SeedImage(
                path=(
                    "/products/media/"
                    "1-5cf-regenerating-valve-dimensions.webp"
                ),
                alt_text=(
                    "D'Acqua Dolce 1.5 cubic foot filtration tank "
                    "with regenerating valve and dimensions"
                ),
                sort_order=0,
            ),
            SeedImage(
                path=(
                    "/products/media/"
                    "dd15catrv-spec-dimensions.webp"
                ),
                alt_text=(
                    "DD15CATRV 1.5cf Catalytic Carbon Filter "
                    "with Regenerating Valve specification dimensions"
                ),
                sort_order=10,
            ),
        ),
    ),
    SeedProduct(
        sku="DD15CAT-TTACPTV",
        name="1.5cf Catalytic Water Conditioner — Pass-through Valve",
        slug="dd15cat-ttacptv",
        description=(
            "1.5 cubic foot catalytic water conditioner configured "
            "with a pass-through valve and prefilter."
        ),
        product_family="Catalytic Water Conditioner",
        category_slug="whole-home-filtration",
        images=(
            SeedImage(
                path=(
                    "/products/media/"
                    "1-5cf-pass-through-with-prefilter-dimensions.webp"
                ),
                alt_text=(
                    "D'Acqua Dolce 1.5 cubic foot water conditioner "
                    "with pass-through valve, prefilter, and dimensions"
                ),
                sort_order=0,
            ),
            SeedImage(
                path=(
                    "/products/media/"
                    "dd15cat-ttacptv-spec-dimensions.webp"
                ),
                alt_text=(
                    "DD15CAT-TTACPTV 1.5cf Catalytic Water Conditioner "
                    "with Pass-through Valve specification dimensions"
                ),
                sort_order=10,
            ),
        ),
    ),
    SeedProduct(
        sku="DD15CAT-TTACRV",
        name="1.5cf Catalytic Water Conditioner — Regenerating Valve",
        slug="dd15cat-ttacrv",
        description=(
            "1.5 cubic foot catalytic water conditioner configured "
            "with a regenerating valve and prefilter."
        ),
        product_family="Catalytic Water Conditioner",
        category_slug="whole-home-filtration",
        images=(
            SeedImage(
                path=(
                    "/products/media/"
                    "1-5cf-regenerating-with-prefilter-dimensions.webp"
                ),
                alt_text=(
                    "D'Acqua Dolce 1.5 cubic foot water conditioner "
                    "with regenerating valve, prefilter, and dimensions"
                ),
                sort_order=0,
            ),
            SeedImage(
                path=(
                    "/products/media/"
                    "dd15cat-ttacrv-spec-dimensions.webp"
                ),
                alt_text=(
                    "DD15CAT-TTACRV 1.5cf Catalytic Water Conditioner "
                    "with Regenerating Valve specification dimensions"
                ),
                sort_order=10,
            ),
        ),
    ),
    SeedProduct(
        sku="DD5RO",
        name="5 Stage Reverse Osmosis",
        slug="dd5ro",
        description="Five-stage reverse osmosis system.",
        product_family="Reverse Osmosis",
        category_slug="reverse-osmosis",
        images=(
            SeedImage(
                path=(
                    "/products/media/"
                    "reverse-osmosis-without-remineralizer-dimensions.webp"
                ),
                alt_text=(
                    "D'Acqua Dolce five-stage reverse osmosis system "
                    "and storage tank with dimensions"
                ),
                sort_order=0,
            ),
            SeedImage(
                path=(
                    "/products/media/"
                    "dd5ro-spec-dimensions.webp"
                ),
                alt_text=(
                    "DD5RO 5 Stage Reverse Osmosis specification dimensions"
                ),
                sort_order=10,
            ),
        ),
    ),
    SeedProduct(
        sku="DD5ROAE",
        name="5 Stage Reverse Osmosis — Alkaline Enhancer",
        slug="dd5roae",
        description=(
            "Five-stage reverse osmosis system with alkaline enhancer."
        ),
        product_family="Reverse Osmosis",
        category_slug="reverse-osmosis",
        images=(
            SeedImage(
                path=(
                    "/products/media/"
                    "reverse-osmosis-with-remineralizer-dimensions.webp"
                ),
                alt_text=(
                    "D'Acqua Dolce reverse osmosis system with "
                    "remineralizer stage and dimensions"
                ),
                sort_order=0,
            ),
            SeedImage(
                path=(
                    "/products/media/"
                    "dd5roae-spec-dimensions.webp"
                ),
                alt_text=(
                    "DD5ROAE 5 Stage Reverse Osmosis with "
                    "Alkaline Enhancer specification dimensions"
                ),
                sort_order=10,
            ),
        ),
    ),
)


def get_or_create_manufacturer(db: object) -> Manufacturer:
    manufacturer = db.scalar(
        select(Manufacturer).where(
            Manufacturer.slug == "dacqua-dolce"
        )
    )

    if manufacturer is None:
        manufacturer = Manufacturer(
            name="D'Acqua Dolce",
            slug="dacqua-dolce",
            public_summary="Water filtration systems.",
        )
        db.add(manufacturer)
        db.flush()

    return manufacturer


def get_or_create_categories(
    db: object,
) -> dict[str, ProductCategory]:
    definitions = (
        (
            "whole-home-filtration",
            "Whole-Home Filtration",
            "Whole-home filtration and conditioning systems.",
            10,
        ),
        (
            "reverse-osmosis",
            "Reverse Osmosis",
            "Point-of-use reverse osmosis systems.",
            20,
        ),
    )

    categories: dict[str, ProductCategory] = {}

    for slug, name, description, sort_order in definitions:
        category = db.scalar(
            select(ProductCategory).where(
                ProductCategory.slug == slug
            )
        )

        if category is None:
            category = ProductCategory(
                name=name,
                slug=slug,
                description=description,
                sort_order=sort_order,
            )
            db.add(category)
            db.flush()

        categories[slug] = category

    return categories


def ensure_images(
    db: object,
    product: Product,
    images: tuple[SeedImage, ...],
) -> int:
    existing_paths = {
        image.storage_path
        for image in product.images
    }

    created = 0

    for image in images:
        if image.path in existing_paths:
            continue

        db.add(
            ProductImage(
                product_id=product.id,
                storage_path=image.path,
                alt_text=image.alt_text,
                sort_order=image.sort_order,
                active=True,
            )
        )
        created += 1

    return created


def main() -> None:
    created_products = 0
    created_images = 0

    with SessionLocal() as db:
        manufacturer = get_or_create_manufacturer(db)
        categories = get_or_create_categories(db)

        for seed in PRODUCTS:
            product = db.scalar(
                select(Product).where(
                    Product.sku == seed.sku
                )
            )

            if product is None:
                product = Product(
                    manufacturer_id=manufacturer.id,
                    category_id=categories[
                        seed.category_slug
                    ].id,
                    name=seed.name,
                    slug=seed.slug,
                    sku=seed.sku,
                    description=seed.description,
                    product_family=seed.product_family,
                    active=True,
                    public_path=(
                        f"/systems/{seed.slug}"
                    ),
                )
                db.add(product)
                db.flush()
                created_products += 1

            db.refresh(
                product,
                attribute_names=["images"],
            )

            created_images += ensure_images(
                db,
                product,
                seed.images,
            )

        db.commit()

    print(
        "Catalog seed complete: "
        f"{created_products} product(s) created, "
        f"{created_images} image record(s) created."
    )


if __name__ == "__main__":
    main()
