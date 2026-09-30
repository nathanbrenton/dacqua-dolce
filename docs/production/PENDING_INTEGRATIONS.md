# D'Acqua Dolce Pending Production Integrations

This file isolates intentionally unfinished work from the commissioned production runbook. Items remain here until they are implemented and validated on production.

## 1. AWS S3 + restic off-host disaster recovery

Current state:

- local PostgreSQL custom-format backup is commissioned;
- real weekly restore validation is commissioned;
- deployment-time pre-migration backup is commissioned;
- restic is installed/prepared;
- the restic repository password is stored securely and has an off-server copy;
- AWS credentials, bucket, IAM policy, repository initialization, retention, and off-host restore testing are not yet commissioned.

Future milestone must include:

- dedicated private backup bucket;
- dedicated least-privilege IAM identity/role;
- credentials stored only in protected server configuration or an appropriate AWS credential mechanism;
- initialized encrypted restic repository;
- automated copy/snapshot job;
- retention/lifecycle policy;
- `restic check` policy;
- off-host restore rehearsal;
- Prometheus/systemd monitoring of remote-backup freshness/failure;
- documented credential rotation and disaster-recovery procedure.

Do not describe off-host disaster recovery as complete until a restore from the remote repository has been rehearsed successfully.

## 2. Observability report delivery

Generator:

    /usr/local/sbin/dacqua-observability-report.py

Current state:

- dry-run report generation is validated;
- application Postmark transactional email is live and remains reserved for application/customer transactional traffic;
- direct infrastructure-monitoring delivery is intended to use local Postfix/sendmail -> recipient MX so routine status traffic does not consume the limited Postmark allowance;
- Vultr outbound TCP/25 approval is still pending;
- daily D'Acqua Dolce status email was not being received as of 2026-09-30;
- earlier commissioning documentation recorded report timers as disabled; verify the actual current timer/service state during diagnosis and do not newly enable/re-enable recurring delivery until the path is accepted;
- Better Stack report heartbeats remain unsubmitted until the successful-delivery boundary is commissioned.

Desired schedule/recipients remain:

- daily — 09:00 `America/Los_Angeles` -> `nathan@nathanbrenton.com`;
- weekly — Saturday 11:00 `America/Los_Angeles` -> `nathan@nathanbrenton.com` and `jamie.dacqua.dolce@gmail.com`.

Before attributing the missing reports solely to TCP/25, diagnose all boundaries:

1. confirm the report generator renders successfully;
2. inspect installed/disabled report timer and service state;
3. inspect the Postfix queue with `postqueue -p`;
4. inspect Postfix logs with `journalctl -u postfix --no-pager`;
5. confirm the configured recipients;
6. test outbound TCP/25 only against the actual recipient-domain MX after Vultr reports approval.

Acceptance after Vultr approval must prove:

- TCP/25 connectivity to the intended recipient MX;
- the selected sender/envelope domain and Postfix HELO identity are explicit;
- forward DNS and provider-controlled PTR/reverse DNS are appropriate for the selected direct-delivery identity;
- SPF authorization and any DKIM signing required by the selected sender design are deliberately configured rather than assumed;
- a received test message shows the intended SPF/DKIM/DMARC alignment;
- a controlled report is accepted for delivery;
- the recipient actually receives it;
- Postfix queue/log state is clean;
- failure behavior is visible;
- only then are daily/weekly timers enabled;
- the corresponding Better Stack heartbeat is submitted only after successful delivery.

Do not silently fall back to the application Postmark token/allowance merely to make routine observability mail appear functional. If the business later chooses Postmark as the monitoring transport, document and commission that as an explicit architecture change.


## 3. Communications retention, purge, and attachment lifecycle

Commissioned:

- durable PostgreSQL communication threads/messages/recipients/attachments/events;
- authenticated Customer Inbox with Inbox/System/Archived/All views;
- archive/restore workflow with no data destruction;
- employee replies and thread-specific return routing;
- public `support@dacquadolce.com` inbound route through Cloudflare Email Routing -> Postmark -> production webhook;
- safe plain-text URL linkification in the Operations inbox.

Still pending as a business/data-governance decision:

- retention period(s) for customer correspondence;
- retention period(s) for attachment bytes;
- privileged permanent-delete/purge behavior, if any;
- how deletion requests propagate into backup retention and restore procedures;
- legal-hold/privacy-request handling;
- storage-growth thresholds that would justify moving attachment payloads out of PostgreSQL or introducing automated purge.

Do not add a routine hard-delete button merely to keep the Operations page tidy. Archive/restore is the normal workflow control. Permanent deletion should be policy-driven, auditable, and compatible with backup/privacy obligations.

## 4. Observability service systemd hardening

FastAPI systemd hardening is commissioned and validated. The observability services still require incremental hardening where compatible with each vendor unit.

Continue with measured changes rather than copying the FastAPI sandbox wholesale. Alertmanager remains an early candidate because its effective systemd security exposure was materially higher than the hardened API service.

For each service:

- record the current effective unit/drop-ins;
- apply only compatible sandbox controls;
- restart and validate the service/listener;
- verify Prometheus targets/alerts and Grafana health where relevant;
- run a non-interactive `systemd-analyze security ... --no-pager` comparison;
- document the final validated state only.

## 5. Pricing activation, checkout policy, and payment provider

The application preserves a strict third-party hosted/tokenized payment-data boundary, but authoritative production prices and a production payment processor/checkout flow are not yet commissioned.

Before enabling live checkout:

1. populate authoritative backend/database pricing rather than frontend/static prices;
2. confirm MAP/list/cart-only/private-quote/no-online-sale policy per product;
3. define tax, shipping/delivery, installation, deposit, quote-only, and inventory-reservation behavior;
4. select the payment processor;
5. integrate through the existing payment-provider boundary;
6. use sandbox/test mode first;
7. create payment sessions/intents server-side;
8. keep raw PAN/CVV/track/PIN data entirely outside D'Acqua Dolce;
9. authenticate and idempotently process provider webhooks;
10. map provider payment states to internal order states;
11. validate authorization/capture/cancel/refund/failure/retry paths;
12. perform a controlled production acceptance only after the business approves go-live.

## Commissioned items removed from this file

The following are no longer pending and belong in the commissioned production documents:

- durable communications archive;
- outbound communication archival;
- authenticated Postmark inbound webhook;
- real inbound-email archival/idempotency validation;
- authenticated Operations Customer Inbox and threaded employee replies;
- Inbox/System/Archived/All communication-history workflow;
- public `support@dacquadolce.com` inbound routing through Cloudflare Email Routing;
- safe plain-text URL linkification in Customer Inbox.

### PT20.1 payment/order boundary status

The approved-quote-to-order boundary is now implemented in application code: an approved formal quote can produce one authoritative `awaiting_payment` order with immutable line snapshots and an auditable source-quote link. A provider-neutral hosted-checkout orchestration seam is also present and tested without card data.

Production payment remains pending. Before PT20.2, Affinity24 must identify the concrete gateway/account provisioned for D'Acqua Dolce (for example, one of the gateway families they publicly support or another explicitly assigned option) and provide authoritative sandbox credentials, API documentation, webhook authentication/verification rules, idempotency behavior, refund/status semantics, and permitted retained identifiers. Do not enable a customer-facing payment launch merely from Affinity24 marketing material.

### PT20.2A verified-event readiness

The provider-neutral verified-payment-event core is implemented. It gives the
future gateway adapter a narrow authenticated handoff: provider event identity,
normalized payment status, authoritative amount/currency, provider-issued
references, and minimal payment-method display metadata. Provider events are
idempotent and raw webhook payloads are not stored.

A verified successful event may mark an `awaiting_payment` order `paid` only on
an exact amount/currency match. Refund events are recorded without guessing
full/partial-refund policy.

Still required before customer-facing payment can be enabled:

1. the exact Affinity24-provisioned gateway/platform;
2. authoritative sandbox and production endpoint documentation;
3. server-side authentication/credential names;
4. hosted checkout/session creation contract;
5. webhook signature/authentication rules and event identifiers;
6. provider event/status mapping, including asynchronous/out-of-order behavior;
7. refund, void, retry, and idempotency semantics;
8. return/cancel URL requirements;
9. merchant/account identifiers and permitted retained fields;
10. confirmation of enabled payment methods such as ACH.

Do not create an unauthenticated generic payment webhook merely to exercise the
new event core. The public endpoint belongs with the concrete verified adapter.
