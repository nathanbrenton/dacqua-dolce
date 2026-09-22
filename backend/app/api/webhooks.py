import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from app.core.email_config import EmailRuntimeSettings, get_email_runtime_settings
from app.db.session import get_db
from app.schemas.postmark_webhooks import (
    PostmarkInboundWebhook,
    PostmarkInboundWebhookResponse,
)
from app.services.communications_archive import archive_postmark_inbound_email

router = APIRouter(
    prefix="/webhooks/postmark",
    tags=["webhooks"],
)

_basic_auth = HTTPBasic(auto_error=False)


def _require_inbound_webhook_auth(
    credentials: Annotated[HTTPBasicCredentials | None, Depends(_basic_auth)],
    settings: Annotated[EmailRuntimeSettings, Depends(get_email_runtime_settings)],
) -> None:
    expected_username = settings.postmark_inbound_webhook_username_value
    expected_password = settings.postmark_inbound_webhook_password_value

    if expected_username is None or expected_password is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Inbound email webhook is not configured.",
        )

    authenticated = (
        credentials is not None
        and secrets.compare_digest(credentials.username, expected_username)
        and secrets.compare_digest(credentials.password, expected_password)
    )

    if not authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook credentials.",
            headers={"WWW-Authenticate": "Basic"},
        )


@router.post(
    "/inbound",
    response_model=PostmarkInboundWebhookResponse,
    dependencies=[Depends(_require_inbound_webhook_auth)],
)
def receive_postmark_inbound_email(
    payload: PostmarkInboundWebhook,
    db: Annotated[Session, Depends(get_db)],
) -> PostmarkInboundWebhookResponse:
    try:
        result = archive_postmark_inbound_email(
            db,
            payload=payload,
        )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    db.commit()

    return PostmarkInboundWebhookResponse(
        status=("duplicate" if result.duplicate else "received"),
        message_id=payload.message_id,
        communication_message_id=str(result.message.id),
        thread_id=str(result.message.thread_id),
    )
