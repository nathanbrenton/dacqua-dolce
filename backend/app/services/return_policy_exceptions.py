from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import AuditEvent
from app.models.commerce import Order
from app.models.policy import FormalQuotePolicySnapshot, PolicyKind
from app.services.audit import record_audit_event

RETURN_POLICY_EXCEPTION_ACTION = "order.return_policy_exception_authorized"


class ReturnPolicyExceptionError(ValueError):
    pass


@dataclass(frozen=True)
class ReturnPolicyExceptionEvidence:
    id: str
    actor_user_id: str | None
    created_at: datetime
    policy_snapshot_id: str
    policy_version: str
    reason: str
    return_window_days_override: int | None
    restocking_fee_basis_points_override: int | None
    customer_pays_return_shipping_override: bool | None
    refund_outbound_shipping_override: bool | None


def refund_policy_snapshot_for_order(
    db: Session,
    *,
    order: Order,
) -> FormalQuotePolicySnapshot | None:
    if order.formal_quote_id is None:
        return None

    return db.scalar(
        select(FormalQuotePolicySnapshot).where(
            FormalQuotePolicySnapshot.formal_quote_id == order.formal_quote_id,
            FormalQuotePolicySnapshot.kind == PolicyKind.refund,
        )
    )


def authorize_return_policy_exception(
    db: Session,
    *,
    order: Order,
    actor_user_id: uuid.UUID,
    reason: str,
    return_window_days_override: int | None = None,
    restocking_fee_basis_points_override: int | None = None,
    customer_pays_return_shipping_override: bool | None = None,
    refund_outbound_shipping_override: bool | None = None,
) -> AuditEvent:
    cleaned_reason = reason.strip()
    if not cleaned_reason:
        raise ReturnPolicyExceptionError(
            "A reason is required for a return-policy exception."
        )
    if len(cleaned_reason) > 4000:
        raise ReturnPolicyExceptionError(
            "Return-policy exception reason is too long."
        )

    if return_window_days_override is not None and not (
        1 <= return_window_days_override <= 3650
    ):
        raise ReturnPolicyExceptionError(
            "Return-window override must be between 1 and 3650 days."
        )

    if restocking_fee_basis_points_override is not None and not (
        0 <= restocking_fee_basis_points_override <= 10_000
    ):
        raise ReturnPolicyExceptionError(
            "Restocking-fee override must be between 0% and 100%."
        )

    if all(
        value is None
        for value in (
            return_window_days_override,
            restocking_fee_basis_points_override,
            customer_pays_return_shipping_override,
            refund_outbound_shipping_override,
        )
    ):
        raise ReturnPolicyExceptionError(
            "At least one return-policy term must be overridden."
        )

    snapshot = refund_policy_snapshot_for_order(
        db,
        order=order,
    )
    if snapshot is None:
        raise ReturnPolicyExceptionError(
            "This order does not have a snapshotted Refund Policy."
        )

    event = record_audit_event(
        db,
        action=RETURN_POLICY_EXCEPTION_ACTION,
        entity_type="order",
        entity_id=str(order.id),
        actor_user_id=actor_user_id,
        metadata={
            "refund_policy_snapshot_id": str(snapshot.id),
            "refund_policy_version": snapshot.version_snapshot,
            "reason": cleaned_reason,
            "return_window_days_override": return_window_days_override,
            "restocking_fee_basis_points_override": (
                restocking_fee_basis_points_override
            ),
            "customer_pays_return_shipping_override": (
                customer_pays_return_shipping_override
            ),
            "refund_outbound_shipping_override": (
                refund_outbound_shipping_override
            ),
        },
    )
    db.flush()
    return event


def _optional_int(value: object) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _optional_bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def list_return_policy_exceptions(
    db: Session,
    *,
    order_id: uuid.UUID,
) -> list[ReturnPolicyExceptionEvidence]:
    events = db.scalars(
        select(AuditEvent)
        .where(
            AuditEvent.action == RETURN_POLICY_EXCEPTION_ACTION,
            AuditEvent.entity_type == "order",
            AuditEvent.entity_id == str(order_id),
        )
        .order_by(
            AuditEvent.created_at.desc(),
            AuditEvent.id.desc(),
        )
    ).all()

    result: list[ReturnPolicyExceptionEvidence] = []
    for event in events:
        metadata = (
            event.metadata_json
            if isinstance(event.metadata_json, dict)
            else {}
        )
        policy_snapshot_id = metadata.get("refund_policy_snapshot_id")
        policy_version = metadata.get("refund_policy_version")
        reason = metadata.get("reason")
        if not all(
            isinstance(value, str) and value
            for value in (
                policy_snapshot_id,
                policy_version,
                reason,
            )
        ):
            continue

        result.append(
            ReturnPolicyExceptionEvidence(
                id=str(event.id),
                actor_user_id=(
                    str(event.actor_user_id)
                    if event.actor_user_id is not None
                    else None
                ),
                created_at=event.created_at,
                policy_snapshot_id=policy_snapshot_id,
                policy_version=policy_version,
                reason=reason,
                return_window_days_override=_optional_int(
                    metadata.get("return_window_days_override")
                ),
                restocking_fee_basis_points_override=_optional_int(
                    metadata.get("restocking_fee_basis_points_override")
                ),
                customer_pays_return_shipping_override=_optional_bool(
                    metadata.get("customer_pays_return_shipping_override")
                ),
                refund_outbound_shipping_override=_optional_bool(
                    metadata.get("refund_outbound_shipping_override")
                ),
            )
        )

    return result
