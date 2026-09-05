import secrets
from collections.abc import Awaitable, Callable
from typing import ClassVar

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from app.core.config import Settings


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def issue_csrf_cookie(
    response: Response,
    settings: Settings,
    *,
    token: str | None = None,
) -> str:
    csrf_token = token or generate_csrf_token()

    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        max_age=settings.csrf_token_max_age_seconds,
        path="/",
    )

    response.headers[settings.csrf_response_header_name] = csrf_token

    return csrf_token


def clear_csrf_cookie(
    response: Response,
    settings: Settings,
) -> None:
    response.delete_cookie(
        key=settings.csrf_cookie_name,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite=settings.session_cookie_samesite,
    )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    sensitive_prefixes: ClassVar[tuple[str, ...]] = (
        "/api/auth",
        "/api/admin",
        "/api/operations",
        "/api/portal",
        "/api/payments",
    )

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["X-DNS-Prefetch-Control"] = "off"

        if request.url.path.startswith(self.sensitive_prefixes):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"

        return response


class CSRFMiddleware(BaseHTTPMiddleware):
    unsafe_methods: ClassVar[frozenset[str]] = frozenset({"POST", "PUT", "PATCH", "DELETE"})

    def __init__(
        self,
        app: ASGIApp,
        settings: Settings,
    ) -> None:
        super().__init__(app)
        self.settings = settings

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if self.settings.csrf_protection_enabled and request.method in self.unsafe_methods:
            cookie_token = request.cookies.get(self.settings.csrf_cookie_name)
            header_token = request.headers.get(self.settings.csrf_request_header_name)

            if (
                cookie_token is None
                or header_token is None
                or not secrets.compare_digest(
                    cookie_token,
                    header_token,
                )
            ):
                return JSONResponse(
                    {"detail": "CSRF validation failed."},
                    status_code=403,
                )

        return await call_next(request)
