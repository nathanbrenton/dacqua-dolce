"""Verify Cloudflare Turnstile tokens on the server, never in the browser alone."""

import httpx
from fastapi import HTTPException, Request

from app.core.config import get_settings

VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def verify_public_form_turnstile(request: Request, *, action: str) -> None:
    settings = get_settings()
    if not settings.turnstile_enabled:
        return
    if not settings.turnstile_secret or not settings.turnstile_expected_hostname:
        raise HTTPException(status_code=503, detail="Form verification is unavailable.")
    token = request.headers.get("X-Turnstile-Token", "")
    if not token or len(token) > 2048:
        raise HTTPException(status_code=400, detail="Complete the verification challenge.")
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.post(
                VERIFY_URL,
                data={"secret": settings.turnstile_secret, "response": token},
            )
            response.raise_for_status()
            result = response.json()
    except (httpx.HTTPError, ValueError):
        raise HTTPException(
            status_code=503, detail="Verification is temporarily unavailable."
        ) from None
    if (
        not isinstance(result, dict)
        or result.get("success") is not True
        or result.get("hostname") != settings.turnstile_expected_hostname
        or result.get("action") != action
    ):
        raise HTTPException(status_code=400, detail="Verification failed. Please try again.")
