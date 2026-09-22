import uuid

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


def test_postmark_thread_reply_to_uses_mailbox_hash() -> None:
    thread_id = uuid.UUID("11111111-2222-3333-4444-555555555555")
    settings = EmailRuntimeSettings(
        postmark_inbound_address="abc123@inbound.postmarkapp.com",
    )

    assert settings.postmark_thread_reply_to(thread_id) == (
        "abc123+11111111-2222-3333-4444-555555555555"
        "@inbound.postmarkapp.com"
    )


def test_postmark_inbound_address_rejects_plus_alias() -> None:
    with pytest.raises(ValidationError):
        EmailRuntimeSettings(
            postmark_inbound_address=(
                "abc123+already-threaded@inbound.postmarkapp.com"
            )
        )
