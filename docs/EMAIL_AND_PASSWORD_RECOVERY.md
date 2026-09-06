# D'Acqua Dolce — Transactional Email and Password Recovery

## Provider

P0 transactional email uses Postmark through an application adapter.

Public application code does not send mail through a self-hosted public
SMTP server.

Local development defaults to:

    DACQUA_EMAIL_PROVIDER=disabled

so no message is sent until Postmark is explicitly configured.

## Required production settings

    DACQUA_PUBLIC_ORIGIN=https://<canonical-public-host>
    DACQUA_EMAIL_PROVIDER=postmark
    DACQUA_POSTMARK_SERVER_TOKEN=<secret>
    DACQUA_EMAIL_FROM=<verified-sender>
    DACQUA_EMAIL_OPERATOR_TO=<business-inbox>
    DACQUA_PASSWORD_RESET_TTL_MINUTES=30

Secrets belong in deployment/runtime secret configuration, never Git.

## Canonical reset URLs

Password reset links are constructed only from the explicitly configured
`DACQUA_PUBLIC_ORIGIN`.

Request Host headers are never used to construct reset links.

Remote origins are required to use HTTPS. Plain HTTP is accepted only for
localhost development.

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

When the application moves to multiple app nodes, authentication and reset
rate-limit state should move to an appropriate shared backend.

## Email delivery records

`email_deliveries` tracks operational delivery state without retaining
rendered message bodies or raw provider payloads.

Stored operational fields include:

- category;
- sender and recipient;
- subject;
- delivery status;
- provider name;
- provider message/reference identifier;
- bounded error summary;
- related application entity.

## Quote workflow

A quote request remains durable even if email delivery fails.

The application attempts:

1. a receipt to the customer;
2. an operator notification when `DACQUA_EMAIL_OPERATOR_TO` is configured.

Delivery outcome is recorded separately from quote state.
