# D'Acqua Dolce — Transactional Email, Email Verification, and Password Recovery

## Provider

P0 application transactional email and customer correspondence use Postmark
through the FastAPI application adapter.

Production live sending through the verified `dacquadolce.com` sending domain
is commissioned. Public application code does not send mail through a
self-hosted public SMTP server.

Local development defaults to:

    DACQUA_EMAIL_PROVIDER=disabled

so no message is sent until Postmark is intentionally configured.

The Postmark application adapter imports runtime `httpx`. The separate
development dependency `httpx2` exists for Starlette/FastAPI test-client
compatibility and does not replace the Postmark runtime dependency.

## Required production settings

The production configuration includes the following non-secret identities and
secret placeholders:

    DACQUA_PUBLIC_ORIGIN=https://dacquadolce.com
    DACQUA_EMAIL_PROVIDER=postmark
    DACQUA_POSTMARK_SERVER_TOKEN=<secret>
    DACQUA_POSTMARK_INBOUND_ADDRESS=<private-provider-address>
    DACQUA_POSTMARK_INBOUND_WEBHOOK_USERNAME=<secret>
    DACQUA_POSTMARK_INBOUND_WEBHOOK_PASSWORD=<secret>
    DACQUA_EMAIL_FROM=no-reply@dacquadolce.com
    DACQUA_EMAIL_SUPPORT_FROM=support@dacquadolce.com
    DACQUA_EMAIL_REPLY_FROM_ADDRESSES=sales@dacquadolce.com,contact@dacquadolce.com,info@dacquadolce.com,support@dacquadolce.com
    DACQUA_EMAIL_SENDER_NAME="D'Acqua Dolce"
    DACQUA_EMAIL_OPERATOR_TO=<business-inbox>
    DACQUA_PASSWORD_RESET_TTL_MINUTES=30
    DACQUA_EMAIL_VERIFICATION_TTL_MINUTES=<configured-ttl>

Quote the sender display name exactly as shown when it is stored in a shell
environment file. The apostrophe in `D'Acqua Dolce` makes the unquoted form
unsafe shell syntax.

Secrets belong in root-controlled deployment/runtime configuration, never Git.
The production application reads its Postmark token and private inbound routing
configuration from `/etc/dacqua-dolce/backend.env`.

The visible display name is added at the Postmark delivery boundary. The
PostgreSQL communications archive retains the canonical bare sender address,
such as `sales@dacquadolce.com`.

### Mail identities are not staff login identities

The approved role addresses (`sales@`, `contact@`, `info@`, `support@`, and
`no-reply@`) are application mail identities. The authenticated human staff
account remains the author/audit actor for an Operations reply.

Do not create generic production application accounts such as
`developer@dacquadolce.com` or `admin@dacquadolce.com` merely to match
development fixtures or mail roles. Production staff access belongs to real
individual identities; hosted human mailboxes are a separate business-email
decision.

## Canonical public URLs

Password-reset and email-verification links are constructed only from the
explicitly configured `DACQUA_PUBLIC_ORIGIN`.

Request Host headers are never used to construct security-sensitive links.

Remote origins are required to use HTTPS. Plain HTTP is accepted only for
localhost development.

## Email verification security

Registration email verification uses random, single-use, expiring tokens:

- tokens are generated with `secrets.token_urlsafe(48)`;
- only SHA-256 token hashes are stored;
- issuing a new verification token supersedes prior unused tokens;
- successful verification consumes the token and supersedes remaining unused
  tokens;
- raw verification tokens are not stored in the database or delivery records;
- issuance and completion generate audit events;
- IP/account request limits are applied in-process for P0.

The verification URL is a landing page only. Opening the URL does **not**
consume the token. The customer must explicitly select **Verify email address**,
which submits the token to the verification endpoint. This protects the flow
from ordinary link scanners, email-security crawlers, and browser prefetches
that may perform a GET before the customer acts.

In production, an unverified account is not treated as fully authenticated
until verification succeeds.

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

When the application moves to multiple app nodes, authentication, verification,
and reset rate-limit state should move to an appropriate shared backend.

## Delivery ledger and durable communications archive

`email_deliveries` tracks operational transport state. It is not the
correspondence body archive.

Stored delivery-ledger fields include:

- category;
- sender and recipient;
- subject;
- delivery status;
- provider name;
- provider message/reference identifier;
- bounded error summary;
- related application entity.

Durable customer/company correspondence is archived separately in PostgreSQL
through:

- `communication_threads`;
- `communication_messages`;
- `communication_recipients`;
- `communication_attachments`;
- `communication_events`.

Full correspondence bodies may therefore be retained intentionally without
turning the transport ledger into a mailbox table. Authentication/recovery
secrets are redacted in the durable archive where required.

## Quote workflow

A quote request remains durable even if email delivery fails.

The application attempts a customer receipt and an operator notification when
configured. Delivery outcome is recorded separately from quote state.

Quote-request replies from Operations prefer the visible company sender roles
in this order:

    sales -> contact -> info -> support -> no-reply

Other customer-conversation replies prefer:

    support -> contact -> info -> sales -> no-reply

The internal authenticated employee remains the author/audit actor.

## Inbound and employee communications

The shared-inbox workflow is commissioned:

    inbound message
      -> Cloudflare Email Routing
      -> Postmark inbound stream
      -> authenticated FastAPI webhook
      -> PostgreSQL communications archive
      -> Operations Customer Inbox

    employee reply
      -> authenticated Operations UI
      -> FastAPI
      -> PostgreSQL archive
      -> Postmark HTTPS API
      -> customer

A private thread-aware Postmark address is used only as `Reply-To`; it is not
shown as the visible company sender.

Employees work from the authenticated D'Acqua Dolce application rather than
requiring the production server to operate a general-purpose IMAP mailbox.

## Mail-authentication validation

SPF and DKIM have passed live delivery checks. A previous Gmail **Show
original** inspection reported DMARC FAIL. Treat DMARC alignment as an
outstanding audit item until a new live message is explicitly revalidated as
DMARC PASS; do not document DMARC as healthy merely because SPF/DKIM pass.
