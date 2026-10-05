import uuid
from dataclasses import dataclass
from typing import Literal, Protocol

GatewayEnvironment = Literal["sandbox", "production"]
GatewayIntegrationMode = Literal["hosted", "tokenized"]


@dataclass(frozen=True)
class PaymentProviderCapabilities:
    """Facts that must come from the provisioned gateway contract.

    These flags are deliberately descriptive rather than inferred from a
    provider brand. A concrete adapter must populate them from authoritative
    gateway documentation/onboarding evidence.
    """

    hosted_checkout: bool = False
    tokenized_card_entry: bool = False
    authenticated_webhooks: bool = False
    durable_event_ids: bool = False
    idempotent_checkout: bool = False
    refunds: bool = False
    partial_refunds: bool = False
    voids: bool = False


@dataclass(frozen=True)
class PaymentProviderDescriptor:
    """Non-secret provider commissioning metadata exposed by an adapter."""

    gateway: str
    environment: GatewayEnvironment
    integration_mode: GatewayIntegrationMode
    source_reference: str
    capabilities: PaymentProviderCapabilities
    production_commissioned: bool = False


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
    idempotency_key: str


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


@dataclass(frozen=True)
class PaymentRefundRequest:
    """Provider-neutral refund command boundary.

    PT45 intentionally does not expose this through an API or Operations UI.
    A concrete gateway must define authoritative refund semantics first.
    """

    provider_payment_id: str
    amount_minor: int
    currency: str
    idempotency_key: str


@dataclass(frozen=True)
class PaymentVoidRequest:
    """Provider-neutral pre-settlement void command boundary."""

    provider_payment_id: str
    idempotency_key: str


@dataclass(frozen=True)
class PaymentOperationResult:
    """Minimal safe provider result for a future void/refund command."""

    provider: str
    provider_operation_id: str
    status: str


class PaymentProviderAdapter(Protocol):
    @property
    def descriptor(self) -> PaymentProviderDescriptor:
        """Return the gateway facts used to authorize checkout orchestration."""
        ...

    def create_checkout_session(
        self,
        request: CheckoutSessionRequest,
    ) -> CheckoutSessionResult:
        """Create a hosted/tokenized provider checkout session."""
        ...


class PaymentSettlementAdapter(Protocol):
    """Future provider command surface; deliberately not commissioned by PT45."""

    @property
    def descriptor(self) -> PaymentProviderDescriptor:
        ...

    def refund_payment(
        self,
        request: PaymentRefundRequest,
    ) -> PaymentOperationResult:
        ...

    def void_payment(
        self,
        request: PaymentVoidRequest,
    ) -> PaymentOperationResult:
        ...
