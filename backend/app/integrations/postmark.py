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
        sender_name: str | None = None,
        timeout_seconds: float = 10.0,
        message_stream: str = "outbound",
    ) -> None:
        self._server_token = server_token
        self._sender_name = sender_name
        self._timeout_seconds = timeout_seconds
        self._message_stream = message_stream

    def _from_value(
        self,
        sender: str,
    ) -> str:
        if self._sender_name is None:
            return sender

        return f"{self._sender_name} <{sender}>"

    @staticmethod
    def _rejection_detail(
        response: httpx.Response,
    ) -> tuple[int | None, str | None]:
        try:
            data = response.json()
        except ValueError:
            return None, None

        if not isinstance(data, dict):
            return None, None

        error_code = data.get("ErrorCode")
        message = data.get("Message")

        try:
            parsed_code = (
                int(error_code)
                if error_code is not None
                else None
            )
        except (TypeError, ValueError):
            parsed_code = None

        parsed_message = (
            str(message).strip()
            if message is not None
            else None
        )

        return (
            parsed_code,
            parsed_message or None,
        )

    @classmethod
    def _raise_http_rejection(
        cls,
        response: httpx.Response,
    ) -> None:
        error_code, message = cls._rejection_detail(response)

        details = [f"HTTP {response.status_code}"]

        if error_code is not None:
            details.append(f"code {error_code}")

        suffix = f": {message}" if message else ""

        raise RuntimeError(
            "Postmark rejected the message "
            f"({', '.join(details)}){suffix}"
        )

    def send(
        self,
        message: EmailMessage,
    ) -> EmailSendResult:
        payload: dict[str, object] = {
            "From": self._from_value(message.sender),
            "To": message.recipient,
            "Subject": message.subject,
            "TextBody": message.body_text,
            "MessageStream": self._message_stream,
        }

        if message.body_html is not None:
            payload["HtmlBody"] = message.body_html

        if message.reply_to is not None:
            payload["ReplyTo"] = message.reply_to

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

        if response.is_error:
            self._raise_http_rejection(response)

        data = response.json()

        error_code = int(data.get("ErrorCode", 0))

        if error_code != 0:
            message_text = str(
                data.get("Message") or ""
            ).strip()
            suffix = (
                f": {message_text}"
                if message_text
                else ""
            )
            raise RuntimeError(
                "Postmark rejected the message "
                f"(code {error_code}){suffix}"
            )

        reference = data.get("MessageID")

        return EmailSendResult(
            provider_reference=(str(reference) if reference is not None else None)
        )
