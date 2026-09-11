from datetime import UTC, datetime

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.catalog import (
    Product,
    ProductSpecification,
)
from app.models.identity import (
    UserSession,
    UserStatus,
)
from app.schemas.catalog import (
    CatalogDocumentRead,
    CatalogImageRead,
    CatalogPricingRead,
    CatalogProductDetailRead,
    CatalogProductListResponse,
    CatalogProductRead,
    CatalogSpecificationRead,
    CatalogVariantRead,
)
from app.services.pricing import (
    resolve_pricing,
    select_effective_price,
)
from app.services.sessions import hash_session_token

router = APIRouter(
    prefix="/catalog",
    tags=["catalog"],
)

settings = get_settings()


def request_is_authenticated(
    request: Request,
) -> bool:
    token = request.cookies.get(settings.session_cookie_name)

    if token is None:
        return False

    with SessionLocal() as db:
        session_record = db.scalar(
            select(UserSession)
            .options(selectinload(UserSession.user))
            .where(
                UserSession.token_hash == hash_session_token(token),
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > datetime.now(UTC),
            )
        )

        return session_record is not None and session_record.user.status == UserStatus.active


def public_specification_reads(
    specifications: list[ProductSpecification],
) -> list[CatalogSpecificationRead]:
    public_specifications = [
        specification
        for specification in specifications
        if specification.public
        and specification.active
        and specification.verified_at is not None
    ]

    public_specifications.sort(
        key=lambda specification: (
            specification.sort_order,
            specification.spec_key,
        )
    )

    return [
        CatalogSpecificationRead(
            spec_key=specification.spec_key,
            label=specification.label,
            value_text=specification.value_text,
            unit=specification.unit,
        )
        for specification in public_specifications
    ]


def pricing_read(
    product: Product,
    *,
    authenticated: bool,
) -> CatalogPricingRead:
    price = select_effective_price(
        product.prices,
    )
    decision = resolve_pricing(
        price,
        authenticated=authenticated,
    )

    return CatalogPricingRead(
        mode=decision.mode.value,
        amount_minor=(decision.amount_minor if decision.display_price else None),
        currency=decision.currency,
        display_price=decision.display_price,
        can_add_to_cart=decision.can_add_to_cart,
        can_checkout_online=(decision.can_checkout_online),
        action=decision.action,
        action_label=decision.action_label,
    )


@router.get(
    "/products",
    response_model=CatalogProductListResponse,
)
def list_public_products(
    request: Request,
) -> CatalogProductListResponse:
    authenticated = request_is_authenticated(request)

    with SessionLocal() as db:
        products = db.scalars(
            select(Product)
            .options(
                selectinload(Product.manufacturer),
                selectinload(Product.category),
                selectinload(Product.images),
                selectinload(Product.prices),
            )
            .where(Product.active.is_(True))
            .order_by(Product.name)
        ).all()

        result: list[CatalogProductRead] = []

        for product in products:
            active_images = [image for image in product.images if image.active]

            primary_image = active_images[0] if active_images else None

            result.append(
                CatalogProductRead(
                    id=str(product.id),
                    name=product.name,
                    slug=product.slug,
                    sku=product.sku,
                    description=(product.description),
                    product_family=(product.product_family),
                    manufacturer=(product.manufacturer.name),
                    category=(product.category.name),
                    public_path=(product.public_path),
                    primary_image=(
                        CatalogImageRead(
                            path=(primary_image.storage_path),
                            alt_text=(primary_image.alt_text),
                        )
                        if primary_image is not None
                        else None
                    ),
                    pricing=pricing_read(
                        product,
                        authenticated=(authenticated),
                    ),
                )
            )

        return CatalogProductListResponse(products=result)


@router.get(
    "/products/{slug}",
    response_model=CatalogProductDetailRead,
)
def get_public_product(
    slug: str,
    request: Request,
) -> CatalogProductDetailRead:
    authenticated = request_is_authenticated(request)

    with SessionLocal() as db:
        product = db.scalar(
            select(Product)
            .options(
                selectinload(Product.manufacturer),
                selectinload(Product.category),
                selectinload(Product.images),
                selectinload(Product.prices),
                selectinload(Product.variants),
                selectinload(Product.documents),
                selectinload(Product.specifications),
            )
            .where(
                Product.slug == slug,
                Product.active.is_(True),
            )
        )

        if product is None:
            raise HTTPException(
                status_code=(status.HTTP_404_NOT_FOUND),
                detail="System not found.",
            )

        active_images = [
            CatalogImageRead(
                path=image.storage_path,
                alt_text=image.alt_text,
            )
            for image in product.images
            if image.active
        ]

        primary_image = active_images[0] if active_images else None

        return CatalogProductDetailRead(
            id=str(product.id),
            name=product.name,
            slug=product.slug,
            sku=product.sku,
            description=product.description,
            product_family=(product.product_family),
            manufacturer=(product.manufacturer.name),
            category=product.category.name,
            public_path=product.public_path,
            primary_image=primary_image,
            pricing=pricing_read(
                product,
                authenticated=authenticated,
            ),
            images=active_images,
            variants=[
                CatalogVariantRead(
                    id=str(variant.id),
                    display_name=(variant.display_name),
                    sku=variant.sku,
                    option_values=(variant.option_values),
                )
                for variant in product.variants
                if variant.active
            ],
            documents=[
                CatalogDocumentRead(
                    title=document.title,
                    document_type=(document.document_type.value),
                    path=(document.storage_path),
                    content_type=(document.content_type),
                    version=document.version,
                )
                for document in product.documents
                if document.active
            ],
            specifications=public_specification_reads(
                product.specifications,
            ),
        )
