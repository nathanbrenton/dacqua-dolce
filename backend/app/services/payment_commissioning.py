from dataclasses import dataclass

from app.services.payment_provider import PaymentProviderDescriptor


class PaymentProviderCommissioningError(ValueError):
    pass


@dataclass(frozen=True)
class PaymentProviderCommissioningAssessment:
    ready_for_checkout: bool
    missing_requirements: tuple[str, ...]


def _clean_required(value: str, *, field_name: str, max_length: int) -> str:
    normalized = value.strip()
    if not normalized:
        raise PaymentProviderCommissioningError(f"{field_name} is required.")
    if len(normalized) > max_length:
        raise PaymentProviderCommissioningError(
            f"{field_name} exceeds the supported length."
        )
    return normalized


def assess_payment_provider_descriptor(
    descriptor: PaymentProviderDescriptor,
) -> PaymentProviderCommissioningAssessment:
    """Assess only facts supplied by a concrete gateway adapter.

    This function does not infer capabilities from the name Affinity24 or from
    a gateway brand. Production commissioning remains explicit.
    """

    _clean_required(
        descriptor.gateway,
        field_name="payment gateway",
        max_length=80,
    )
    _clean_required(
        descriptor.source_reference,
        field_name="payment gateway source reference",
        max_length=500,
    )

    missing: list[str] = []
    capabilities = descriptor.capabilities

    if descriptor.integration_mode == "hosted":
        if not capabilities.hosted_checkout:
            missing.append("hosted checkout capability")
    elif descriptor.integration_mode == "tokenized":
        if not capabilities.tokenized_card_entry:
            missing.append("tokenized card-entry capability")
    else:  # pragma: no cover - Literal is defense-in-depth at runtime
        missing.append("supported hosted/tokenized integration mode")

    if not capabilities.authenticated_webhooks:
        missing.append("authenticated webhook contract")
    if not capabilities.durable_event_ids:
        missing.append("durable provider event identifiers")
    if not capabilities.idempotent_checkout:
        missing.append("idempotent checkout creation")

    if capabilities.partial_refunds and not capabilities.refunds:
        missing.append("full refund capability required by partial-refund support")

    if descriptor.environment == "production":
        if not descriptor.production_commissioned:
            missing.append("explicit production commissioning")
    elif descriptor.environment != "sandbox":  # pragma: no cover
        missing.append("supported sandbox/production environment")

    return PaymentProviderCommissioningAssessment(
        ready_for_checkout=not missing,
        missing_requirements=tuple(missing),
    )


def require_payment_provider_ready_for_checkout(
    descriptor: PaymentProviderDescriptor,
) -> None:
    assessment = assess_payment_provider_descriptor(descriptor)
    if assessment.ready_for_checkout:
        return

    raise PaymentProviderCommissioningError(
        "Payment provider is not commissioned for hosted checkout: "
        + "; ".join(assessment.missing_requirements)
        + "."
    )
