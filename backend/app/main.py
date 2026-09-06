from fastapi import FastAPI

from app.api.authentication import (
    router as authentication_router,
)
from app.api.catalog import router as catalog_router
from app.api.health import router as health_router
from app.api.quotes import router as quotes_router
from app.core.config import get_settings
from app.core.security import (
    CSRFMiddleware,
    SecurityHeadersMiddleware,
)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    docs_url="/api/docs",
    redoc_url=None,
)

app.add_middleware(
    CSRFMiddleware,
    settings=settings,
)

app.add_middleware(
    SecurityHeadersMiddleware,
)

app.include_router(health_router)

app.include_router(
    authentication_router,
    prefix=settings.api_prefix,
)

app.include_router(
    catalog_router,
    prefix=settings.api_prefix,
)

app.include_router(
    quotes_router,
    prefix=settings.api_prefix,
)
