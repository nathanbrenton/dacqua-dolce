"""Regression coverage for PT32 public inquiry-origin validation."""

import pytest
from fastapi import HTTPException

from app.api.quotes import resolve_inquiry_context
from app.schemas.quote import QuoteRequestCreate


def test_legacy_api_payload_remains_compatible():
    payload = QuoteRequestCreate(name="Test", email="test@example.com")
    assert payload.inquiry_context == "legacy_quote_request"


def test_explicit_expert_inquiry():
    payload = QuoteRequestCreate(
        name="Test", email="test@example.com", inquiry_context="expert_inquiry"
    )
    assert payload.inquiry_context == "expert_inquiry"


@pytest.mark.parametrize(
    ("product_id", "recommendation_context", "declared", "expected"),
    [
        (None, object(), "expert_inquiry", "expert_inquiry"),
        (None, None, "expert_inquiry", "expert_inquiry"),
        (None, object(), "recommendation_inquiry", "recommendation_inquiry"),
        ("product-uuid", None, "product_inquiry", "product_inquiry"),
        ("product-uuid", object(), "product_inquiry", "product_inquiry"),
        (None, None, "legacy_quote_request", "legacy_quote_request"),
        (None, object(), "legacy_quote_request", "legacy_quote_request"),
        ("product-uuid", None, "legacy_quote_request", "legacy_quote_request"),
    ],
)
def test_valid_inquiry_classifications(product_id, recommendation_context, declared, expected):
    assert resolve_inquiry_context(
        product_id=product_id,
        recommendation_context=recommendation_context,
        inquiry_context=declared,
    ) == expected


@pytest.mark.parametrize(
    ("product_id", "recommendation_context", "declared"),
    [
        ("product-uuid", None, "expert_inquiry"),
        ("product-uuid", object(), "recommendation_inquiry"),
        (None, None, "recommendation_inquiry"),
        (None, None, "product_inquiry"),
        (None, object(), "product_inquiry"),
    ],
)
def test_incompatible_inquiry_context_rejected(product_id, recommendation_context, declared):
    with pytest.raises(HTTPException) as error:
        resolve_inquiry_context(
            product_id=product_id,
            recommendation_context=recommendation_context,
            inquiry_context=declared,
        )
    assert error.value.status_code == 422
    assert error.value.detail == "Inquiry context does not match the request."
