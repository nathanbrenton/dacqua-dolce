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

## 2. Better Stack report-delivery heartbeats

Direct observability report delivery is no longer pending.

Commissioned on 2026-10-01:

- `/usr/local/sbin/dacqua-observability-report.py` renders daily/weekly reports;
- `/usr/local/sbin/dacqua-observability-send-report` submits them through local Postfix;
- Vultr outbound TCP/25 is approved and validated;
- `mailout.dacquadolce.com` forward/PTR identity is aligned;
- SPF authorizes `144.202.114.17`;
- OpenDKIM selector `infra2026` signs direct infrastructure mail;
- a controlled daily report was received successfully;
- `dacqua-observability-daily-report.timer` is enabled/active for 09:00 `America/Los_Angeles`;
- `dacqua-observability-weekly-report.timer` is enabled/active for Saturday 11:00 `America/Los_Angeles`.

The remaining integration is the Better Stack successful-delivery heartbeat boundary.

Heartbeat acceptance must ensure:

1. heartbeat submission happens only after the report send path returns successfully;
2. a rendering failure, sendmail/Postfix failure, or other failed report run does not submit a success heartbeat;
3. heartbeat credentials/URLs remain in protected configuration rather than Git/docs;
4. daily and weekly heartbeat resources map to the corresponding report schedules;
5. one controlled successful run updates the intended heartbeat;
6. failure behavior is observable without generating duplicate report mail.

Do not route routine reports through the application Postmark allowance merely to simplify heartbeat integration.


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


## Automated sales tax — PT44 foundation

**Status:** Foundation implemented; production commissioning still required.

PT44 introduces a provider-neutral automated-tax domain and a Stripe Tax
test-mode adapter. Product tax classifications require an exact provider code
and a recorded authoritative source; no default code is inferred. Draft quotes
and awaiting-payment orders can hold sanitized provider calculation evidence,
and hosted checkout fails closed without current authoritative order tax
evidence.

PT44 intentionally rejects live Stripe credentials. Before production checkout,
D’Acqua Dolce still needs:

- authoritative product tax-code review and completion;
- required tax registrations/compliance setup in the tax provider;
- live account/credential commissioning;
- confirmation of filing/reporting operations for externally processed
  Affinity24 payments;
- concrete Affinity24 payment-success/refund integration so Stripe Tax
  transactions and reversals can be committed idempotently;
- explicit taxability rules for currently blocked adjustment types such as
  shipping insurance, discounts, installation, and custom charges.

Stripe Tax is used only as the tax engine in this design. It does not replace
Affinity24 as the intended payment provider.

## Payment provider — PT45 gateway-contract foundation

**Status:** Provider-neutral commissioning boundary implemented; exact Affinity24
gateway still required.

PT45 requires every future concrete payment adapter to declare its exact gateway
identity, sandbox/production environment, hosted/tokenized integration mode,
authoritative contract source, and documented capabilities. Hosted checkout is
rejected unless the adapter establishes authenticated webhooks, durable provider
event IDs, idempotent checkout creation, and the required hosted/tokenized
card-entry capability. Production adapters require explicit commissioning.

Affinity24's public solutions page currently lists multiple gateway options
(Authorize.Net, iPOS, FluidPay, and NMI), so the application intentionally does
not select one based on marketing material. Obtain the gateway actually
provisioned for D'Acqua Dolce plus its sandbox/API/webhook/refund/void contract
before implementing the concrete adapter.

PT45 also defines card-data-free provider-neutral refund and void command
interfaces. They are not wired to public/customer/Operations actions and do not
change refund policy or payment state. Commission those commands only after the
provisioned gateway semantics and D'Acqua Dolce refund/cancellation workflow are
reconciled.
