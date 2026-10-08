# PT32 Phase A — anonymous quote acknowledgement isolation

The public Support form does **not** send automatic acknowledgement mail.
The Quote/Inquiry form records the originating request independently from customer acknowledgement delivery. Optional operator notifications are disabled in commissioned production by leaving `DACQUA_EMAIL_OPERATOR_TO` empty; customer acknowledgement decisions remain independently enforced.

Runtime settings in the protected production environment (never Git):

- `DACQUA_QUOTE_ACK_ENABLED=true` (commissioned production; code/config template defaults **false** until provider validation)
- `DACQUA_QUOTE_ACK_MESSAGE_STREAM=website-acknowledgements` (commissioned **Transactional** stream; never `outbound`)
- `DACQUA_QUOTE_ACK_RECIPIENT_COOLDOWN_HOURS=24`
- `DACQUA_QUOTE_ACK_GLOBAL_LIMIT_PER_HOUR=20`

Commission the stream in the appropriate Postmark server account, record the
exact ID in protected runtime config, validate sender/domain approval and
delivery, then explicitly enable acknowledgements. Do not invent the ID.
Keep critical account/order emails on the original `outbound` stream.

Decision evidence is persisted in existing email_deliveries and communication
archive rows with `quote_customer_receipt` category. Suppressions use bounded
codes: `acknowledgements_disabled`, `acknowledgement_stream_unconfigured`,
`recipient_cooldown`, `global_acknowledgement_limit`.
Provider errors retain existing failure status. The message is a generic
fixed template including only the generated reference UUID. No customer text
or arbitrary URLs are echoed back.

PostgreSQL transaction-level advisory locking serializes acknowledgement
decisions across API workers for the same database; limits count attempted
(pending/sent/failed) acknowledgement rows, not suppressed rows. Existing
historical quote receipt delivery rows count toward the windows. The lock is
held through the Postmark HTTP send and DB commit. This protects concurrency
but can delay simultaneous quote submissions and is *not* a full durable
asynchronous outbox. If the database commit fails after a provider acceptance,
an acknowledgement can be sent without surviving local evidence; do not
promise exactly-once delivery.

These settings do not change IP throttling, CSRF, honeypot, or phone rules.
Phase B Managed Turnstile is commissioned in production; see `PT32_TURNSTILE.md`. A durable asynchronous email outbox remains future work.

Before promotion: run full backend tests, Ruff, frontend build, and
integration acceptance against a configured PostgreSQL test environment.
No production activation without commissioning and approval.
