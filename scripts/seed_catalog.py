"""Idempotently seed the initial D'Acqua Dolce catalog from owner-supplied SKU sheets.

This seed intentionally contains no prices and no health/performance claims.
Pricing therefore resolves conservatively through the application's
NO_ONLINE_PRICE behavior until authoritative business pricing is loaded.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.catalog import (
    Manufacturer,
    Product,
    ProductCategory,
    ProductImage,
    ProductSpecification,
)
from app.services.catalog_seed import (
    reconcile_product_metadata,
    reconcile_specification_metadata,
)


@dataclass(frozen=True)
class SeedImage:
    path: str
    alt_text: str
    sort_order: int


@dataclass(frozen=True)
class SeedSpecification:
    spec_key: str
    label: str
    value_text: str
    unit: str | None
    public: bool
    sort_order: int
    source_reference: str | None = None


@dataclass(frozen=True)
class SeedProduct:
    sku: str
    name: str
    slug: str
    description: str
    product_family: str
    category_slug: str
    specifications: tuple[SeedSpecification, ...]
    images: tuple[SeedImage, ...]


PRODUCTS = (
    SeedProduct(
        sku="DD15CATPTV",
        name="Refine - Pass-Through",
        slug="dd15catptv",
        description=(
            "Whole-home catalytic carbon filtration system with "
            "1.5 cubic feet of media and a pass-through valve."
        ),
        product_family="Catalytic Carbon Filter",
        category_slug="whole-home-filtration",
        specifications=(
            SeedSpecification(
                spec_key="media_volume",
                label="Media Volume",
                value_text="1.5",
                unit="cu ft",
                public=True,
                sort_order=10,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CATPTV.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="valve_type",
                label="Valve Type",
                value_text="Pass-Through",
                unit=None,
                public=True,
                sort_order=20,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CATPTV.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="system_height",
                label="System Height",
                value_text="58",
                unit="in",
                public=True,
                sort_order=40,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CATPTV.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="media_tank_width",
                label="Media Tank Width",
                value_text="11",
                unit="in",
                public=True,
                sort_order=50,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CATPTV.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="dimension_tolerance",
                label="Dimension Tolerance",
                value_text="±0.5",
                unit="in",
                public=False,
                sort_order=90,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CATPTV.jpg"
                ),
            ),
        ),
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
        name="Refine - Regenerating",
        slug="dd15catrv",
        description=(
            "Whole-home catalytic carbon filtration system with "
            "1.5 cubic feet of media and a regenerating valve."
        ),
        product_family="Catalytic Carbon Filter",
        category_slug="whole-home-filtration",
        specifications=(
            SeedSpecification(
                spec_key="media_volume",
                label="Media Volume",
                value_text="1.5",
                unit="cu ft",
                public=True,
                sort_order=10,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CATRV.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="valve_type",
                label="Valve Type",
                value_text="Regenerating",
                unit=None,
                public=True,
                sort_order=20,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CATRV.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="system_height",
                label="System Height",
                value_text="62",
                unit="in",
                public=True,
                sort_order=40,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CATRV.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="media_tank_width",
                label="Media Tank Width",
                value_text="11",
                unit="in",
                public=True,
                sort_order=50,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CATRV.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="dimension_tolerance",
                label="Dimension Tolerance",
                value_text="±0.5",
                unit="in",
                public=False,
                sort_order=90,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CATRV.jpg"
                ),
            ),
        ),
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
        name="Harmony - Pass-Through",
        slug="dd15cat-ttacptv",
        description=(
            "Whole-home catalytic water conditioning system with "
            "1.5 cubic feet of media, a pass-through valve, and prefilter."
        ),
        product_family="Catalytic Water Conditioner",
        category_slug="whole-home-filtration",
        specifications=(
            SeedSpecification(
                spec_key="media_volume",
                label="Media Volume",
                value_text="1.5",
                unit="cu ft",
                public=True,
                sort_order=10,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CAT-TTACPTV.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="valve_type",
                label="Valve Type",
                value_text="Pass-Through",
                unit=None,
                public=True,
                sort_order=20,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CAT-TTACPTV.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="prefilter",
                label="Prefilter",
                value_text="Included",
                unit=None,
                public=True,
                sort_order=30,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CAT-TTACPTV.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="system_height",
                label="System Height",
                value_text="58",
                unit="in",
                public=True,
                sort_order=40,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CAT-TTACPTV.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="media_tank_width",
                label="Media Tank Width",
                value_text="11",
                unit="in",
                public=True,
                sort_order=50,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CAT-TTACPTV.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="prefilter_height",
                label="Prefilter Housing Height",
                value_text="29",
                unit="in",
                public=True,
                sort_order=60,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CAT-TTACPTV.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="prefilter_width",
                label="Prefilter Housing Width",
                value_text="7.5",
                unit="in",
                public=True,
                sort_order=70,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CAT-TTACPTV.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="dimension_tolerance",
                label="Dimension Tolerance",
                value_text="±0.5",
                unit="in",
                public=False,
                sort_order=90,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CAT-TTACPTV.jpg"
                ),
            ),
        ),
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
        name="Harmony - Regenerating",
        slug="dd15cat-ttacrv",
        description=(
            "Whole-home catalytic water conditioning system with "
            "1.5 cubic feet of media, a regenerating valve, and prefilter."
        ),
        product_family="Catalytic Water Conditioner",
        category_slug="whole-home-filtration",
        specifications=(
            SeedSpecification(
                spec_key="media_volume",
                label="Media Volume",
                value_text="1.5",
                unit="cu ft",
                public=True,
                sort_order=10,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CAT-TTACRV.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="valve_type",
                label="Valve Type",
                value_text="Regenerating",
                unit=None,
                public=True,
                sort_order=20,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CAT-TTACRV.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="prefilter",
                label="Prefilter",
                value_text="Included",
                unit=None,
                public=True,
                sort_order=30,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CAT-TTACRV.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="system_height",
                label="System Height",
                value_text="62",
                unit="in",
                public=True,
                sort_order=40,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CAT-TTACRV.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="media_tank_width",
                label="Media Tank Width",
                value_text="11",
                unit="in",
                public=True,
                sort_order=50,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CAT-TTACRV.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="prefilter_height",
                label="Prefilter Housing Height",
                value_text="29",
                unit="in",
                public=True,
                sort_order=60,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CAT-TTACRV.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="prefilter_width",
                label="Prefilter Housing Width",
                value_text="7.5",
                unit="in",
                public=True,
                sort_order=70,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CAT-TTACRV.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="dimension_tolerance",
                label="Dimension Tolerance",
                value_text="±0.5",
                unit="in",
                public=False,
                sort_order=90,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD15CAT-TTACRV.jpg"
                ),
            ),
        ),
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
        name="Origin",
        slug="dd5ro",
        description="Five-stage point-of-use reverse osmosis drinking water system.",
        product_family="Reverse Osmosis",
        category_slug="reverse-osmosis",
        specifications=(
            SeedSpecification(
                spec_key="stage_count",
                label="Stages",
                value_text="5",
                unit=None,
                public=True,
                sort_order=10,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD5RO.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="system_width",
                label="System Width",
                value_text="15",
                unit="in",
                public=True,
                sort_order=20,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD5RO.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="system_height",
                label="System Height",
                value_text="16",
                unit="in",
                public=True,
                sort_order=30,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD5RO.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="storage_tank_width",
                label="Storage Tank Width",
                value_text="11",
                unit="in",
                public=True,
                sort_order=40,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD5RO.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="storage_tank_height",
                label="Storage Tank Height",
                value_text="16",
                unit="in",
                public=True,
                sort_order=50,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD5RO.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="dimension_tolerance",
                label="Dimension Tolerance",
                value_text="±0.5",
                unit="in",
                public=False,
                sort_order=60,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD5RO.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="ro_membrane_model",
                label="RO Membrane",
                value_text="Pentair GRO-50EN",
                unit=None,
                public=True,
                sort_order=70,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD5RO.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="ro_membrane_nominal_flow",
                label="RO Membrane Nominal Flow",
                value_text="50",
                unit="GPD",
                public=True,
                sort_order=80,
                source_reference=(
                    "Pentair GRO Membrane Spec Sheet, GRO-50EN: "
                    "https://www.pentair.com/content/dam/extranet/web/nam/"
                    "pentair/spec-sheets/english/"
                    "4002874-gro-membrane-spec-sheet.pdf"
                ),
            ),
        ),
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
        name="Origin - Alkaline Remineralization",
        slug="dd5roae",
        description=(
            "Five-stage point-of-use reverse osmosis drinking water system "
            "with an alkaline remineralization stage."
        ),
        product_family="Reverse Osmosis",
        category_slug="reverse-osmosis",
        specifications=(
            SeedSpecification(
                spec_key="stage_count",
                label="Stages",
                value_text="5",
                unit=None,
                public=True,
                sort_order=10,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD5ROAE.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="remineralization",
                label="Remineralization",
                value_text="Alkaline",
                unit=None,
                public=True,
                sort_order=20,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD5ROAE.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="system_width",
                label="System Width",
                value_text="15",
                unit="in",
                public=True,
                sort_order=30,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD5ROAE.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="system_height",
                label="System Height",
                value_text="18",
                unit="in",
                public=True,
                sort_order=40,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD5ROAE.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="storage_tank_width",
                label="Storage Tank Width",
                value_text="11",
                unit="in",
                public=True,
                sort_order=50,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD5ROAE.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="storage_tank_height",
                label="Storage Tank Height",
                value_text="16",
                unit="in",
                public=True,
                sort_order=60,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD5ROAE.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="dimension_tolerance",
                label="Dimension Tolerance",
                value_text="±0.5",
                unit="in",
                public=False,
                sort_order=70,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD5ROAE.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="ro_membrane_model",
                label="RO Membrane",
                value_text="Pentair GRO-50EN",
                unit=None,
                public=True,
                sort_order=80,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD5ROAE.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="ro_membrane_nominal_flow",
                label="RO Membrane Nominal Flow",
                value_text="50",
                unit="GPD",
                public=True,
                sort_order=90,
                source_reference=(
                    "Pentair GRO Membrane Spec Sheet, GRO-50EN: "
                    "https://www.pentair.com/content/dam/extranet/web/nam/"
                    "pentair/spec-sheets/english/"
                    "4002874-gro-membrane-spec-sheet.pdf"
                ),
            ),
            SeedSpecification(
                spec_key="alkaline_cartridge_model",
                label="Alkaline Cartridge",
                value_text="K-FLOW K5650 BB",
                unit=None,
                public=True,
                sort_order=100,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD5ROAE.jpg"
                ),
            ),
            SeedSpecification(
                spec_key="alkaline_media",
                label="Alkaline Media",
                value_text="Custom Alkaline Media",
                unit=None,
                public=True,
                sort_order=110,
                source_reference=(
                    "owner-supplied image: "
                    "dacqua-dolce-business/04_Brand_and_Creative/"
                    "Product_Imagery/skudims/DD5ROAE.jpg"
                ),
            ),
        ),
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


def ensure_specifications(
    db: object,
    product: Product,
    specifications: tuple[SeedSpecification, ...],
    *,
    source_reference: str,
) -> int:
    existing = {
        specification.spec_key: specification
        for specification in db.scalars(
            select(ProductSpecification).where(
                ProductSpecification.product_id == product.id
            )
        ).all()
    }

    created = 0

    for seed in specifications:
        effective_source_reference = (
            seed.source_reference
            or source_reference
        )

        specification = existing.get(seed.spec_key)

        if specification is None:
            db.add(
                ProductSpecification(
                    product_id=product.id,
                    spec_key=seed.spec_key,
                    label=seed.label,
                    value_text=seed.value_text,
                    unit=seed.unit,
                    source_reference=effective_source_reference,
                    public=seed.public,
                    sort_order=seed.sort_order,
                    active=True,
                    verified_at=datetime.now(UTC),
                )
            )
            created += 1
            continue

        reconcile_specification_metadata(
            specification,
            label=seed.label,
            value_text=seed.value_text,
            unit=seed.unit,
            source_reference=effective_source_reference,
            public=seed.public,
            sort_order=seed.sort_order,
        )

    return created


def main() -> None:
    created_products = 0
    created_images = 0
    created_specifications = 0

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
            else:
                reconcile_product_metadata(
                    product,
                    manufacturer_id=manufacturer.id,
                    category_id=categories[
                        seed.category_slug
                    ].id,
                    name=seed.name,
                    description=seed.description,
                    product_family=seed.product_family,
                    public_path=(
                        f"/systems/{seed.slug}"
                    ),
                )

            db.refresh(
                product,
                attribute_names=["images"],
            )

            created_images += ensure_images(
                db,
                product,
                seed.images,
            )

            created_specifications += ensure_specifications(
                db,
                product,
                seed.specifications,
                source_reference=(
                    f"owner-supplied SKU sheet: {seed.sku}"
                ),
            )

        db.commit()

    print(
        "Catalog seed complete: "
        f"{created_products} product(s) created, "
        f"{created_images} image record(s) created, "
        f"{created_specifications} specification record(s) created."
    )


if __name__ == "__main__":
    main()
