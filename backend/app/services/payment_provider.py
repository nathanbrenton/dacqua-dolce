import uuid
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CheckoutSessionRequest:
    """Safe request passed from D'Acqua Dolce to a PCI provider.

    Card data is intentionally absent. Card entry must occur only
    on the contracted provider's PCI-compliant surface.
    """

    order_id: uuid.UUID
    amount_minor: int
    currency: str
    customer_email: str
    success_url: str
    cancel_url: str


@dataclass(frozen=True)
class CheckoutSessionResult:
    provider: str
    checkout_session_id: str
    redirect_url: str


@dataclass(frozen=True)
class PaymentMethodDisplay:
    """Minimal provider-supplied payment display metadata."""

    method_type: str | None = None
    brand: str | None = None
    last4: str | None = None


class PaymentProviderAdapter(Protocol):
    def create_checkout_session(
        self,
        request: CheckoutSessionRequest,
    ) -> CheckoutSessionResult:
        """Create a hosted/tokenized provider checkout session."""
        ...
