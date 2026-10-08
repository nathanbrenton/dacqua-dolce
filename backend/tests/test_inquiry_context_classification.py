from app.schemas.quote import QuoteRequestCreate


def test_legacy_api_payload_remains_compatible():
    payload = QuoteRequestCreate(name="Test", email="test@example.com")
    assert payload.inquiry_context == "legacy_quote_request"


def test_explicit_expert_inquiry():
    payload = QuoteRequestCreate(
        name="Test", email="test@example.com", inquiry_context="expert_inquiry"
    )
    assert payload.inquiry_context == "expert_inquiry"
