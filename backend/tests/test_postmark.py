import json

import httpx
import pytest

from app.integrations.email import EmailMessage
from app.integrations.postmark import PostmarkEmailProvider


def _message() -> EmailMessage:
    return EmailMessage(
        sender="no-reply@dacquadolce.com",
        recipient="customer@example.com",
        subject="Test",
        body_text="Body must never appear in provider errors.",
    )


def test_postmark_http_error_includes_provider_code_and_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(*args: object, **kwargs: object) -> httpx.Response:
        request = httpx.Request("POST", PostmarkEmailProvider.API_URL)
        return httpx.Response(
            422,
            request=request,
            json={
                "ErrorCode": 412,
                "Message": "Account is pending approval.",
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    provider = PostmarkEmailProvider(server_token="secret")

    with pytest.raises(
        RuntimeError,
        match=(
            r"Postmark rejected the message "
            r"\(HTTP 422, code 412\): Account is pending approval\."
        ),
    ):
        provider.send(_message())


def test_postmark_http_error_does_not_persist_response_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = "Body must never appear in provider errors."

    def fake_post(*args: object, **kwargs: object) -> httpx.Response:
        request = httpx.Request("POST", PostmarkEmailProvider.API_URL)
        return httpx.Response(
            422,
            request=request,
            content=json.dumps(
                {
                    "ErrorCode": 300,
                    "Message": "Invalid From address.",
                    "EchoedBody": body,
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    provider = PostmarkEmailProvider(server_token="secret")

    with pytest.raises(RuntimeError) as exc_info:
        provider.send(_message())

    message = str(exc_info.value)

    assert "Invalid From address." in message
    assert body not in message
    assert "EchoedBody" not in message


def test_postmark_success_with_nonzero_error_code_includes_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(*args: object, **kwargs: object) -> httpx.Response:
        request = httpx.Request("POST", PostmarkEmailProvider.API_URL)
        return httpx.Response(
            200,
            request=request,
            json={
                "ErrorCode": 406,
                "Message": "Inactive recipient.",
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    provider = PostmarkEmailProvider(server_token="secret")

    with pytest.raises(
        RuntimeError,
        match=(
            r"Postmark rejected the message "
            r"\(code 406\): Inactive recipient\."
        ),
    ):
        provider.send(_message())


def test_postmark_send_includes_reply_to(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_post(*args: object, **kwargs: object) -> httpx.Response:
        captured.update(kwargs)
        request = httpx.Request("POST", PostmarkEmailProvider.API_URL)
        return httpx.Response(
            200,
            request=request,
            json={
                "ErrorCode": 0,
                "Message": "OK",
                "MessageID": "provider-message-id",
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    message = EmailMessage(
        sender="no-reply@dacquadolce.com",
        recipient="customer@example.com",
        subject="Test reply",
        body_text="Reply body",
        reply_to=(
            "abc123+11111111-2222-3333-4444-555555555555"
            "@inbound.postmarkapp.com"
        ),
    )

    PostmarkEmailProvider(server_token="secret").send(message)

    payload = captured["json"]
    assert isinstance(payload, dict)
    assert payload["ReplyTo"] == message.reply_to
