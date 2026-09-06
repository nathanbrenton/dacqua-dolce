from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EmailMessage:
    sender: str
    recipient: str
    subject: str
    body_text: str
    body_html: str | None = None


@dataclass(frozen=True)
class EmailSendResult:
    provider_reference: str | None


class EmailProviderAdapter(Protocol):
    def send(
        self,
        message: EmailMessage,
    ) -> EmailSendResult:
        """Send one message through the configured provider."""
        ...
