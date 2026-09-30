from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.email_config import EmailRuntimeSettings
from app.integrations.email import EmailMessage
from app.models.catalog import (
    ProductRelationship,
    ReminderPreferenceKind,
)
from app.models.customer import (
    CustomerCommunicationPreferences,
    CustomerEquipment,
)
from app.models.email import EmailDeliveryStatus
from app.models.identity import User, UserStatus
from app.models.maintenance import (
    MaintenanceReminder,
    MaintenanceReminderStatus,
)
from app.services.audit import record_audit_event
from app.services.email_delivery import deliver_email
from app.services.post_purchase import next_replacement_due_on

PREFERENCE_FIELDS: dict[ReminderPreferenceKind, str] = {
    ReminderPreferenceKind.filter_replacement: "filter_replacement_reminders",
    ReminderPreferenceKind.uv_service: "uv_service_reminders",
    ReminderPreferenceKind.product_specific: "product_specific_reminders",
}


@dataclass(frozen=True)
class MaintenanceReminderCandidate:
    user_id: uuid.UUID
    recipient: str
    equipment_id: uuid.UUID
    equipment_name: str
    related_product_id: uuid.UUID
    related_product_name: str
    related_product_path: str
    reminder_kind: ReminderPreferenceKind
    due_on: date
    existing_reminder_id: uuid.UUID | None = None


def reminder_preference_enabled(
    preferences: CustomerCommunicationPreferences | None,
    reminder_kind: ReminderPreferenceKind,
) -> bool:
    if preferences is None:
        return False

    return bool(
        getattr(
            preferences,
            PREFERENCE_FIELDS[reminder_kind],
        )
    )


def due_maintenance_reminders(
    db: Session,
    *,
    as_of: date,
    limit: int | None = None,
) -> list[MaintenanceReminderCandidate]:
    equipment_rows = db.scalars(
        select(CustomerEquipment)
        .where(
            CustomerEquipment.active.is_(True),
            CustomerEquipment.product_id.is_not(None),
        )
        .order_by(CustomerEquipment.created_at)
    ).all()

    results: list[MaintenanceReminderCandidate] = []

    for equipment in equipment_rows:
        user = db.get(User, equipment.user_id)
        if (
            user is None
            or user.status != UserStatus.active
            or user.email_verified_at is None
        ):
            continue

        preferences = db.get(
            CustomerCommunicationPreferences,
            equipment.user_id,
        )
        if preferences is None:
            continue

        relationships = db.scalars(
            select(ProductRelationship)
            .options(selectinload(ProductRelationship.related_product))
            .where(
                ProductRelationship.product_id == equipment.product_id,
                ProductRelationship.active.is_(True),
                ProductRelationship.public.is_(True),
                ProductRelationship.is_consumable.is_(True),
                ProductRelationship.replacement_interval_days.is_not(None),
                ProductRelationship.reminder_preference.is_not(None),
            )
            .order_by(
                ProductRelationship.sort_order,
                ProductRelationship.created_at,
            )
        ).all()

        for relationship in relationships:
            reminder_kind = relationship.reminder_preference
            if reminder_kind is None or not reminder_preference_enabled(
                preferences,
                reminder_kind,
            ):
                continue

            related_product = relationship.related_product
            if not related_product.active:
                continue

            due_on = next_replacement_due_on(
                installed_on=equipment.installed_on,
                last_service_on=equipment.last_service_on,
                replacement_interval_days=relationship.replacement_interval_days,
            )
            if due_on is None or due_on > as_of:
                continue

            existing = db.scalar(
                select(MaintenanceReminder).where(
                    MaintenanceReminder.equipment_id == equipment.id,
                    MaintenanceReminder.related_product_id == related_product.id,
                    MaintenanceReminder.reminder_kind == reminder_kind,
                    MaintenanceReminder.due_on == due_on,
                )
            )
            if (
                existing is not None
                and existing.status
                in {
                    MaintenanceReminderStatus.sent,
                    MaintenanceReminderStatus.suppressed,
                }
            ):
                continue

            results.append(
                MaintenanceReminderCandidate(
                    user_id=user.id,
                    recipient=user.email,
                    equipment_id=equipment.id,
                    equipment_name=equipment.name_snapshot,
                    related_product_id=related_product.id,
                    related_product_name=related_product.name,
                    related_product_path=related_product.public_path,
                    reminder_kind=reminder_kind,
                    due_on=due_on,
                    existing_reminder_id=(
                        existing.id if existing is not None else None
                    ),
                )
            )

            if limit is not None and len(results) >= limit:
                return results

    return results


def maintenance_reminder_message(
    candidate: MaintenanceReminderCandidate,
    *,
    settings: EmailRuntimeSettings,
) -> EmailMessage:
    account_url = settings.public_url("/account")
    product_url = settings.public_url(candidate.related_product_path)
    sender = settings.email_support_from or settings.email_from

    subject = f"Replacement reminder: {candidate.related_product_name}"
    body = "\n".join(
        (
            "D'Acqua Dolce replacement reminder",
            "",
            f"Installed system: {candidate.equipment_name}",
            f"Replacement item: {candidate.related_product_name}",
            f"Replacement target: {candidate.due_on.isoformat()}",
            "",
            "Review your installed equipment and replacement guidance:",
            account_url,
            "",
            "Replacement item:",
            product_url,
            "",
            (
                "This optional reminder was sent because replacement reminders "
                "are enabled in your D'Acqua Dolce account."
            ),
            (
                "You can change reminder preferences at any time from your "
                "account."
            ),
        )
    )

    return EmailMessage(
        sender=sender,
        recipient=candidate.recipient,
        subject=subject,
        body_text=body,
        reply_to=settings.email_support_from,
    )


def dispatch_maintenance_reminder(
    db: Session,
    *,
    candidate: MaintenanceReminderCandidate,
    settings: EmailRuntimeSettings,
    now: datetime | None = None,
) -> MaintenanceReminder:
    attempted_at = now or datetime.now(UTC)

    reminder = (
        db.get(MaintenanceReminder, candidate.existing_reminder_id)
        if candidate.existing_reminder_id is not None
        else None
    )

    if reminder is not None and reminder.status in {
        MaintenanceReminderStatus.sent,
        MaintenanceReminderStatus.suppressed,
    }:
        return reminder

    if reminder is None:
        reminder = MaintenanceReminder(
            user_id=candidate.user_id,
            equipment_id=candidate.equipment_id,
            related_product_id=candidate.related_product_id,
            reminder_kind=candidate.reminder_kind,
            due_on=candidate.due_on,
            recipient=candidate.recipient,
            status=MaintenanceReminderStatus.failed,
            attempted_at=attempted_at,
        )
        db.add(reminder)
        db.flush()
    else:
        reminder.recipient = candidate.recipient
        reminder.attempted_at = attempted_at

    delivery = deliver_email(
        db,
        settings=settings,
        message=maintenance_reminder_message(
            candidate,
            settings=settings,
        ),
        category="maintenance_reminder",
        related_entity_type="maintenance_reminder",
        related_entity_id=str(reminder.id),
        customer_user_id=candidate.user_id,
    )

    reminder.email_delivery_id = delivery.id

    if delivery.status == EmailDeliveryStatus.sent:
        reminder.status = MaintenanceReminderStatus.sent
        reminder.sent_at = delivery.sent_at or attempted_at
    elif delivery.status == EmailDeliveryStatus.suppressed:
        reminder.status = MaintenanceReminderStatus.suppressed
        reminder.sent_at = None
    else:
        reminder.status = MaintenanceReminderStatus.failed
        reminder.sent_at = None

    record_audit_event(
        db,
        action="maintenance.reminder_delivery_attempted",
        entity_type="maintenance_reminder",
        entity_id=str(reminder.id),
        actor_user_id=None,
        metadata={
            "equipment_id": str(candidate.equipment_id),
            "related_product_id": str(candidate.related_product_id),
            "reminder_kind": candidate.reminder_kind.value,
            "due_on": candidate.due_on.isoformat(),
            "delivery_status": delivery.status.value,
        },
    )
    db.flush()

    return reminder
