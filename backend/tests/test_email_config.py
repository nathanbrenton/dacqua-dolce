import pytest
from pydantic import ValidationError

from app.core.email_config import (
    EmailRuntimeSettings,
)


def test_local_http_origin_is_allowed() -> None:
    settings = EmailRuntimeSettings(public_origin=("http://127.0.0.1:5173/"))

    assert settings.public_origin == "http://127.0.0.1:5173"


def test_remote_http_origin_is_rejected() -> None:
    with pytest.raises(ValidationError):
        EmailRuntimeSettings(public_origin=("http://example.com"))


def test_reset_url_uses_configured_origin() -> None:
    settings = EmailRuntimeSettings(public_origin=("https://water.example"))

    assert settings.public_url("/reset-password/example-token") == (
        "https://water.example/reset-password/example-token"
    )
