from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PostmarkInboundAddress(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    email: str = Field(alias="Email", min_length=3, max_length=320)
    name: str = Field(alias="Name", default="", max_length=200)
    mailbox_hash: str = Field(alias="MailboxHash", default="", max_length=300)


class PostmarkInboundHeader(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    name: str = Field(alias="Name", min_length=1, max_length=200)
    value: str = Field(alias="Value", max_length=4000)


class PostmarkInboundAttachment(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    name: str = Field(alias="Name", min_length=1, max_length=500)
    content: str = Field(alias="Content", min_length=1)
    content_type: str = Field(alias="ContentType", min_length=1, max_length=255)
    content_length: int = Field(
        alias="ContentLength",
        ge=0,
        le=35 * 1024 * 1024,
    )
    content_id: str | None = Field(alias="ContentID", default=None, max_length=500)
    content_disposition: str | None = Field(
        alias="ContentDisposition",
        default=None,
        max_length=40,
    )


class PostmarkInboundWebhook(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    from_name: str = Field(alias="FromName", default="", max_length=200)
    message_stream: Literal["inbound"] = Field(alias="MessageStream")
    from_address: str = Field(alias="From", min_length=3, max_length=320)
    from_full: PostmarkInboundAddress = Field(alias="FromFull")
    to: str = Field(alias="To", default="")
    to_full: list[PostmarkInboundAddress] = Field(alias="ToFull", default_factory=list)
    cc: str = Field(alias="Cc", default="")
    cc_full: list[PostmarkInboundAddress] = Field(alias="CcFull", default_factory=list)
    bcc: str = Field(alias="Bcc", default="")
    bcc_full: list[PostmarkInboundAddress] = Field(alias="BccFull", default_factory=list)
    original_recipient: str = Field(alias="OriginalRecipient", default="", max_length=320)
    subject: str = Field(alias="Subject", default="", max_length=300)
    message_id: str = Field(alias="MessageID", min_length=1, max_length=300)
    reply_to: str = Field(alias="ReplyTo", default="", max_length=320)
    mailbox_hash: str = Field(alias="MailboxHash", default="", max_length=300)
    date: str = Field(alias="Date", default="", max_length=200)
    text_body: str = Field(alias="TextBody", default="")
    html_body: str = Field(alias="HtmlBody", default="")
    stripped_text_reply: str = Field(alias="StrippedTextReply", default="")
    tag: str = Field(alias="Tag", default="", max_length=200)
    headers: list[PostmarkInboundHeader] = Field(alias="Headers", default_factory=list)
    attachments: list[PostmarkInboundAttachment] = Field(
        alias="Attachments",
        default_factory=list,
    )
    raw_email: str | None = Field(alias="RawEmail", default=None)


class PostmarkInboundWebhookResponse(BaseModel):
    status: str
    message_id: str
    communication_message_id: str
    thread_id: str
