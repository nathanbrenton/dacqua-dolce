from fastapi import FastAPI

from app.api.account import router as account_router
from app.api.authentication import router as authentication_router
from app.api.cart import router as cart_router
from app.api.catalog import router as catalog_router
from app.api.health import router as health_router
from app.api.operations import router as operations_router
from app.api.orders import router as orders_router
from app.api.password_reset import router as password_reset_router
from app.api.quotes import router as quotes_router
from app.core.config import get_settings
from app.core.security import CSRFMiddleware, SecurityHeadersMiddleware


def create_app(
    settings=None,
) -> FastAPI:
    resolved_settings = (
        settings
        if settings is not None
        else get_settings()
    )

    docs_enabled = (
        not resolved_settings.is_production
    )

    application = FastAPI(
        title=resolved_settings.app_name,
        docs_url=(
            "/api/docs"
            if docs_enabled
            else None
        ),
        redoc_url=None,
        openapi_url=(
            "/openapi.json"
            if docs_enabled
            else None
        ),
    )

    application.add_middleware(
        CSRFMiddleware,
        settings=resolved_settings,
    )
    application.add_middleware(
        SecurityHeadersMiddleware,
        settings=resolved_settings,
    )

    application.include_router(health_router)
    application.include_router(
        authentication_router,
        prefix=resolved_settings.api_prefix,
    )
    application.include_router(
        password_reset_router,
        prefix=resolved_settings.api_prefix,
    )
    application.include_router(
        account_router,
        prefix=resolved_settings.api_prefix,
    )
    application.include_router(
        cart_router,
        prefix=resolved_settings.api_prefix,
    )
    application.include_router(
        catalog_router,
        prefix=resolved_settings.api_prefix,
    )
    application.include_router(
        operations_router,
        prefix=resolved_settings.api_prefix,
    )
    application.include_router(
        orders_router,
        prefix=resolved_settings.api_prefix,
    )
    application.include_router(
        quotes_router,
        prefix=resolved_settings.api_prefix,
    )

    return application


app = create_app()
