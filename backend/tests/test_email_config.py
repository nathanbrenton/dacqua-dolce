import uuid

import pytest
from pydantic import ValidationError

from app.core.email_config import (
    EmailRuntimeSettings,
)


def test_local_http_origin_is_allowed() -> None:
    settings = EmailRuntimeSettings(public_origin=("http://127.0.0.1:15173/"))

    assert settings.public_origin == "http://127.0.0.1:15173"


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

def test_support_sender_is_normalized() -> None:
    settings = EmailRuntimeSettings(
        email_support_from=" Support@DacquaDolce.com ",
    )

    assert settings.email_support_from == "support@dacquadolce.com"


def test_blank_support_sender_uses_fallback_path() -> None:
    settings = EmailRuntimeSettings(
        email_support_from="   ",
    )

    assert settings.email_support_from is None


def test_reply_sender_addresses_are_normalized_and_deduplicated() -> None:
    settings = EmailRuntimeSettings(
        email_from="no-reply@dacquadolce.com",
        email_support_from="support@dacquadolce.com",
        email_reply_from_addresses=(
            " Sales@DacquaDolce.com; info@dacquadolce.com, "
            "sales@dacquadolce.com "
        ),
    )

    assert settings.communication_reply_from_addresses == (
        "sales@dacquadolce.com",
        "info@dacquadolce.com",
        "support@dacquadolce.com",
        "no-reply@dacquadolce.com",
    )


def test_development_environment_uses_safe_test_company_addresses() -> None:
    settings = EmailRuntimeSettings(
        environment="development",
    )

    assert settings.email_from == "no-reply@dacquadolce.test"
    assert settings.communication_reply_from_addresses == (
        "sales@dacquadolce.test",
        "contact@dacquadolce.test",
        "info@dacquadolce.test",
        "support@dacquadolce.test",
        "no-reply@dacquadolce.test",
    )


def test_test_environment_uses_safe_test_company_addresses() -> None:
    settings = EmailRuntimeSettings(
        environment="test",
    )

    assert settings.email_from == "no-reply@dacquadolce.test"
    assert settings.communication_reply_from_addresses[0:4] == (
        "sales@dacquadolce.test",
        "contact@dacquadolce.test",
        "info@dacquadolce.test",
        "support@dacquadolce.test",
    )


def test_production_environment_switches_company_addresses_to_dot_com() -> None:
    settings = EmailRuntimeSettings(
        environment="production",
    )

    assert settings.email_from == "no-reply@dacquadolce.com"
    assert settings.communication_reply_from_addresses == (
        "sales@dacquadolce.com",
        "contact@dacquadolce.com",
        "info@dacquadolce.com",
        "support@dacquadolce.com",
        "no-reply@dacquadolce.com",
    )


def test_configured_reply_senders_override_environment_generated_roles() -> None:
    settings = EmailRuntimeSettings(
        environment="production",
        email_from="no-reply@dacquadolce.com",
        email_reply_from_addresses=(
            "sales@dacquadolce.com,info@dacquadolce.com"
        ),
    )

    assert settings.communication_reply_from_addresses == (
        "sales@dacquadolce.com",
        "info@dacquadolce.com",
        "no-reply@dacquadolce.com",
    )


def test_sender_display_name_defaults_to_company_brand() -> None:
    settings = EmailRuntimeSettings()

    assert settings.email_sender_name == "D'Acqua Dolce"


def test_sender_display_name_is_trimmed() -> None:
    settings = EmailRuntimeSettings(
        email_sender_name="  D'Acqua Dolce  ",
    )

    assert settings.email_sender_name == "D'Acqua Dolce"


@pytest.mark.parametrize(
    "sender_name",
    [
        "",
        "   ",
        "D'Acqua Dolce\nBcc: attacker@example.test",
        "D'Acqua Dolce <spoof@example.test>",
    ],
)
def test_sender_display_name_rejects_unsafe_values(
    sender_name: str,
) -> None:
    with pytest.raises(ValidationError):
        EmailRuntimeSettings(
            email_sender_name=sender_name,
        )
