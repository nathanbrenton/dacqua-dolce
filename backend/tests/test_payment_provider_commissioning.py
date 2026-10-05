import pytest

from app.services.payment_commissioning import (
    PaymentProviderCommissioningError,
    assess_payment_provider_descriptor,
    require_payment_provider_ready_for_checkout,
)
from app.services.payment_provider import (
    PaymentProviderCapabilities,
    PaymentProviderDescriptor,
)


def sandbox_descriptor(**overrides) -> PaymentProviderDescriptor:
    values = {
        "gateway": "sandbox-gateway",
        "environment": "sandbox",
        "integration_mode": "hosted",
        "source_reference": "Authoritative sandbox contract",
        "capabilities": PaymentProviderCapabilities(
            hosted_checkout=True,
            authenticated_webhooks=True,
            durable_event_ids=True,
            idempotent_checkout=True,
        ),
        "production_commissioned": False,
    }
    values.update(overrides)
    return PaymentProviderDescriptor(**values)


def test_sandbox_descriptor_can_satisfy_checkout_contract() -> None:
    assessment = assess_payment_provider_descriptor(sandbox_descriptor())

    assert assessment.ready_for_checkout is True
    assert assessment.missing_requirements == ()
    require_payment_provider_ready_for_checkout(sandbox_descriptor())


def test_descriptor_requires_authoritative_source_reference() -> None:
    with pytest.raises(
        PaymentProviderCommissioningError,
        match="source reference",
    ):
        assess_payment_provider_descriptor(
            sandbox_descriptor(source_reference="   ")
        )


def test_descriptor_requires_authenticated_webhooks_and_event_ids() -> None:
    descriptor = sandbox_descriptor(
        capabilities=PaymentProviderCapabilities(
            hosted_checkout=True,
            idempotent_checkout=True,
        )
    )

    assessment = assess_payment_provider_descriptor(descriptor)

    assert assessment.ready_for_checkout is False
    assert "authenticated webhook contract" in assessment.missing_requirements
    assert "durable provider event identifiers" in assessment.missing_requirements


def test_descriptor_requires_idempotent_checkout_creation() -> None:
    descriptor = sandbox_descriptor(
        capabilities=PaymentProviderCapabilities(
            hosted_checkout=True,
            authenticated_webhooks=True,
            durable_event_ids=True,
        )
    )

    assessment = assess_payment_provider_descriptor(descriptor)

    assert assessment.ready_for_checkout is False
    assert "idempotent checkout creation" in assessment.missing_requirements


def test_tokenized_mode_requires_tokenized_card_entry_capability() -> None:
    descriptor = sandbox_descriptor(
        integration_mode="tokenized",
        capabilities=PaymentProviderCapabilities(
            authenticated_webhooks=True,
            durable_event_ids=True,
            idempotent_checkout=True,
        ),
    )

    assessment = assess_payment_provider_descriptor(descriptor)

    assert assessment.ready_for_checkout is False
    assert "tokenized card-entry capability" in assessment.missing_requirements


def test_production_descriptor_requires_explicit_commissioning() -> None:
    descriptor = sandbox_descriptor(
        environment="production",
        production_commissioned=False,
    )

    with pytest.raises(
        PaymentProviderCommissioningError,
        match="explicit production commissioning",
    ):
        require_payment_provider_ready_for_checkout(descriptor)


def test_partial_refund_claim_requires_refund_capability() -> None:
    descriptor = sandbox_descriptor(
        capabilities=PaymentProviderCapabilities(
            hosted_checkout=True,
            authenticated_webhooks=True,
            durable_event_ids=True,
            idempotent_checkout=True,
            partial_refunds=True,
        )
    )

    assessment = assess_payment_provider_descriptor(descriptor)

    assert assessment.ready_for_checkout is False
    assert (
        "full refund capability required by partial-refund support"
        in assessment.missing_requirements
    )
