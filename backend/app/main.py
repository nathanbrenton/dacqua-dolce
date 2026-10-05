from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response

from app.api.account import router as account_router
from app.api.administration import router as administration_router
from app.api.authentication import router as authentication_router
from app.api.cart import router as cart_router
from app.api.catalog import router as catalog_router
from app.api.health import router as health_router
from app.api.operations import router as operations_router
from app.api.orders import router as orders_router
from app.api.password_reset import router as password_reset_router
from app.api.policies import (
    operations_router as policy_operations_router,
)
from app.api.policies import (
    public_router as policy_public_router,
)
from app.api.quotes import router as quotes_router
from app.api.support import router as support_router
from app.api.webhooks import router as webhooks_router
from app.core.config import get_settings
from app.core.request_context import reset_request_id, set_request_id
from app.core.security import CSRFMiddleware, SecurityHeadersMiddleware


async def request_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = uuid4().hex
    request.state.request_id = request_id
    token = set_request_id(request_id)

    try:
        response = await call_next(request)
    finally:
        reset_request_id(token)

    response.headers["X-Request-ID"] = request_id
    return response


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

    application.middleware("http")(request_id_middleware)

    application.add_middleware(
        CSRFMiddleware,
        settings=resolved_settings,
        exempt_paths=frozenset(
            {
                f"{resolved_settings.api_prefix}/webhooks/postmark/inbound",
            }
        ),
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
        policy_public_router,
        prefix=resolved_settings.api_prefix,
    )
    application.include_router(
        policy_operations_router,
        prefix=resolved_settings.api_prefix,
    )
    application.include_router(
        account_router,
        prefix=resolved_settings.api_prefix,
    )
    application.include_router(
        administration_router,
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
    application.include_router(
        support_router,
        prefix=resolved_settings.api_prefix,
    )
    application.include_router(
        webhooks_router,
        prefix=resolved_settings.api_prefix,
    )

    return application


app = create_app()
