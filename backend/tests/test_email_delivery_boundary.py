from app.models.email import (
    EmailDelivery,
)


def test_email_delivery_does_not_store_message_body() -> None:
    columns = {column.name for column in EmailDelivery.__table__.columns}

    assert "body" not in columns
    assert "body_text" not in columns
    assert "body_html" not in columns
    assert "raw_payload" not in columns
