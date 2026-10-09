import uuid

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.privacy import sanitize_text, sanitize_value
from app.core.request_context import get_request_id
from app.models.audit import AuditEvent


def sanitize_audit_entity_id(value: str) -> str:
    """Preserve canonical UUID entity identifiers without bypassing free-text redaction.

    UUIDs are nonsecret record identifiers. Card-number redaction can otherwise
    mistake adjacent UUID digit groups for a PAN and destroy referential audit data.
    Everything that is not a complete canonical UUID keeps normal sanitization.
    """
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        return sanitize_text(value, max_length=120)
    if str(parsed) == value.lower():
        return str(parsed)
    return sanitize_text(value, max_length=120)


def record_audit_event(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    actor_user_id: uuid.UUID | None = None,
    metadata: dict[str, object] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditEvent:
    safe_metadata = dict(metadata or {})
    request_id = get_request_id()

    if request_id is not None:
        safe_metadata.setdefault(
            "request_id",
            request_id,
        )

    event = AuditEvent(
        actor_user_id=actor_user_id,
        action=sanitize_text(
            action,
            max_length=120,
        ),
        entity_type=sanitize_text(
            entity_type,
            max_length=120,
        ),
        entity_id=(
            sanitize_audit_entity_id(entity_id)
            if entity_id is not None
            else None
        ),
        environment=get_settings().environment,
        metadata_json=sanitize_value(safe_metadata),
        ip_address=(
            sanitize_text(
                ip_address,
                max_length=64,
            )
            if ip_address is not None
            else None
        ),
        user_agent=(
            sanitize_text(
                user_agent,
                max_length=512,
            )
            if user_agent is not None
            else None
        ),
    )

    db.add(event)

    return event
