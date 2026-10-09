"""Regression coverage for audit entity identifiers and privacy sanitization."""

from app.core.privacy import REDACTED, sanitize_text, sanitize_value
from app.services.audit import sanitize_audit_entity_id


def test_uuid_false_positive_examples_preserved():
    # These specific UUIDs previously triggered false payment-card redaction.
    for value in (
        "72132952-8190-406c-80f6-c348f792e3d3",
        "fbcf21d7-1912-4124-8687-76ec9ef71b32",
    ):
        assert sanitize_audit_entity_id(value) == value
        assert REDACTED in sanitize_text(value)


def test_uuid_uppercase_is_canonicalized():
    value = "72132952-8190-406C-80F6-C348F792E3D3"
    assert sanitize_audit_entity_id(value) == value.lower()


def test_non_uuid_query_token_is_redacted():
    result = sanitize_audit_entity_id("reference?token=my-secret-value")
    assert "my-secret-value" not in result
    assert REDACTED in result


def test_non_uuid_payment_card_is_redacted():
    result = sanitize_audit_entity_id("4111 1111 1111 1111")
    assert result == REDACTED


def test_uuid_plus_suffix_is_not_treated_as_uuid():
    result = sanitize_audit_entity_id(
        "72132952-8190-406c-80f6-c348f792e3d3?token=private-secret"
    )
    assert "private-secret" not in result
    assert REDACTED in result


def test_sensitive_metadata_still_redacted():
    result = sanitize_value({"api_key": "secret-value", "nested": {"password": "hidden"}})
    assert result["api_key"] == REDACTED
    assert result["nested"]["password"] == REDACTED
