import httpx

from app.integrations.email import (
    EmailMessage,
    EmailSendResult,
)


class PostmarkEmailProvider:
    API_URL = "https://api.postmarkapp.com/email"

    def __init__(
        self,
        *,
        server_token: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._server_token = server_token
        self._timeout_seconds = timeout_seconds

    def send(
        self,
        message: EmailMessage,
    ) -> EmailSendResult:
        payload: dict[str, object] = {
            "From": message.sender,
            "To": message.recipient,
            "Subject": message.subject,
            "TextBody": message.body_text,
            "MessageStream": "outbound",
        }

        if message.body_html is not None:
            payload["HtmlBody"] = message.body_html

        response = httpx.post(
            self.API_URL,
            headers={
                "Accept": "application/json",
                "Content-Type": ("application/json"),
                "X-Postmark-Server-Token": (self._server_token),
            },
            json=payload,
            timeout=self._timeout_seconds,
        )

        response.raise_for_status()

        data = response.json()

        error_code = int(data.get("ErrorCode", 0))

        if error_code != 0:
            raise RuntimeError(f"Postmark rejected the message (code {error_code}).")

        reference = data.get("MessageID")

        return EmailSendResult(
            provider_reference=(str(reference) if reference is not None else None)
        )
