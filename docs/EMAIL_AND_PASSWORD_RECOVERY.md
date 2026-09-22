# D'Acqua Dolce — Transactional Email, Email Verification, and Password Recovery

## Provider

P0 application transactional email uses Postmark through the FastAPI application adapter.

Production live sending through the verified `dacquadolce.com` sending domain was validated on 2026-09-22. Public application code does not send mail through a self-hosted public SMTP server.

Local development defaults to:

    DACQUA_EMAIL_PROVIDER=disabled

so no message is sent until Postmark is explicitly configured.

The Postmark application adapter imports runtime `httpx`. The separate development dependency `httpx2` exists for Starlette/FastAPI test-client compatibility and does not replace the Postmark runtime dependency.

## Required production settings

    DACQUA_PUBLIC_ORIGIN=https://dacquadolce.com
    DACQUA_EMAIL_PROVIDER=postmark
    DACQUA_POSTMARK_SERVER_TOKEN=<secret>
    DACQUA_EMAIL_FROM=<verified-sender>
    DACQUA_EMAIL_OPERATOR_TO=<business-inbox>
    DACQUA_PASSWORD_RESET_TTL_MINUTES=30
    DACQUA_EMAIL_VERIFICATION_TTL_MINUTES=<configured-ttl>

Secrets belong in root-controlled deployment/runtime configuration, never Git. The production application currently reads its Postmark token from `/etc/dacqua-dolce/backend.env`.

Postmark API failures retain a bounded provider error description for operational diagnosis, including HTTP status and Postmark `ErrorCode`/`Message` when supplied. Raw provider payloads and rendered message bodies are not persisted.

## Canonical public URLs

Password-reset and email-verification links are constructed only from the explicitly configured `DACQUA_PUBLIC_ORIGIN`.

Request Host headers are never used to construct security-sensitive links.

Remote origins are required to use HTTPS. Plain HTTP is accepted only for localhost development.

## Email verification security

Registration email verification uses random, single-use, expiring tokens:

- tokens are generated with `secrets.token_urlsafe(48)`;
- only SHA-256 token hashes are stored;
- issuing a new verification token supersedes prior unused tokens;
- successful verification consumes the token and supersedes remaining unused tokens;
- raw verification tokens are not stored in the database or delivery records;
- issuance and completion generate audit events;
- IP/account request limits are applied in-process for P0.

The verification URL is a landing page only. Opening the URL does **not** consume the token. The customer must explicitly select **Verify email address**, which submits the token to the verification endpoint. This protects the flow from ordinary link scanners, email-security crawlers, and browser prefetches that may perform a GET before the customer acts.

In production, an unverified account is not treated as fully authenticated until verification succeeds.

## Password-reset security

Reset behavior is intentionally designed around these constraints:

- request responses do not reveal whether an account exists;
- reset tokens are generated with `secrets.token_urlsafe(48)`;
- only SHA-256 token hashes are stored;
- tokens expire after 30 minutes by default;
- issuing a new token supersedes prior unused tokens;
- tokens are single-use;
- tokens become invalid if the password changed after issuance;
- successful reset clears lockout counters;
- successful reset revokes all existing sessions;
- reset requests and completions generate audit events;
- IP/account request limits are applied in-process for P0;
- raw tokens are not stored in the database or email-delivery records.

When the application moves to multiple app nodes, authentication, verification, and reset rate-limit state should move to an appropriate shared backend.

## Email delivery records

`email_deliveries` tracks operational delivery state without retaining rendered message bodies or raw provider payloads.

Stored operational fields include:

- category;
- sender and recipient;
- subject;
- delivery status;
- provider name;
- provider message/reference identifier;
- bounded error summary;
- related application entity.

This table is **not** the future customer-communications archive. The planned communications system must use dedicated thread/message/recipient/attachment/delivery-event records so durable business correspondence can be retained intentionally rather than weakening the metadata-only delivery boundary.

## Quote workflow

A quote request remains durable even if email delivery fails.

The application attempts:

1. a receipt to the customer;
2. an operator notification when `DACQUA_EMAIL_OPERATOR_TO` is configured.

Delivery outcome is recorded separately from quote state.

## Inbound and employee communications

Postmark is the application transport, but a complete inbound employee/shared-inbox workflow is not yet commissioned.

The planned application boundary is:

    inbound reply -> Postmark inbound webhook -> FastAPI -> PostgreSQL communications archive

    employee reply -> authenticated web Operations UI -> FastAPI -> PostgreSQL archive -> Postmark API

Customer/company communications should become durably archived in PostgreSQL. Employees should work from the authenticated D'Acqua Dolce web application rather than requiring the production server to operate a general-purpose IMAP mailbox.
