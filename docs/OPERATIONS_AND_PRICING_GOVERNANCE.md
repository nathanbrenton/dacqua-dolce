# D'Acqua Dolce — Operations, Account Administration, and Pricing Governance

## Purpose

The Operations console keeps operational business decisions on the
authenticated server side instead of hard-coding them into the customer
frontend.

The current console order is:

1. Customer Inbox
2. Customer Requests
3. Customer Orders
4. Pricing & Inventory
5. Accounts & Address Book
6. User Access & Roles
7. Audit Log

The order is intentional and should remain consistent between local and
production builds unless a later UX milestone explicitly changes it.

## Capability boundary

Backend authorization is authoritative. Frontend role visibility and disabled
controls are UX only.

| Capability | Employee | Administrator | Developer |
| --- | --- | --- | --- |
| Customer Inbox and customer communications | yes | yes | yes |
| Requests/orders and ordinary Operations work | yes | yes | yes |
| Pricing & Inventory read | yes | yes | yes |
| Pricing & Inventory write | no | yes | yes |
| Customer equipment write | no | yes | yes |
| User Access & Roles administration | no | yes | yes |
| Audit Log read | no | no | yes |

The legacy `manager` enum remains for compatibility with historical
assignments. It continues to satisfy ordinary Operations access while being
phased out, but it cannot be newly assigned and is not a canonical fixture.

Customer accounts do not receive Operations access merely by registering.

Privileged roles remain subject to the application's MFA policy.

## Account administration safeguards

Ordinary web administration is intentionally narrower than developer
provisioning.

Current safeguards include:

- a staff account may have at most one web-managed staff role;
- the legacy `manager` role cannot be newly assigned;
- an administrator cannot remove their own administrator role;
- the final active administrator cannot be removed;
- developer accounts are rejected by the web role editor;
- successful web changes emit audit events;
- developer provisioning/recovery remains an out-of-band CLI action;
- deliberate conversion to one staff-only role uses the guarded
  `set-staff-role` CLI command rather than ad-hoc SQL.

The CLI also protects the final active developer.

## Pricing-policy governance

Price values are authoritative database records. Prices must never be embedded
in frontend source code, static HTML, CSS, SEO metadata, or generated marketing
content.

Supported product-level policy modes:

- `PUBLIC`
- `MAP_LIMITED`
- `CART_ONLY`
- `PRIVATE_QUOTE`
- `LOGIN_REQUIRED`
- `NO_ONLINE_PRICE`
- `NO_ONLINE_SALE`

Modes that support an online transaction or visible authenticated/public price
require an authoritative amount:

- `PUBLIC`
- `MAP_LIMITED`
- `CART_ONLY`
- `LOGIN_REQUIRED`

Restricted modes deliberately reject a stored online amount:

- `PRIVATE_QUOTE`
- `NO_ONLINE_PRICE`
- `NO_ONLINE_SALE`

This prevents the console from becoming a workaround for a manufacturer rule
that prohibits online price display or online sale.

Employees receive read-only Pricing & Inventory access. Mutation controls are
disabled in the UI for employees, and FastAPI independently rejects unauthorized
writes. Administrators and developers may perform pricing/inventory mutations.

## Historical pricing

A pricing change does not overwrite the prior row. The prior active
product-level pricing record is closed with `effective_until` and marked
inactive, then a new active pricing record is created.

## Inventory

P0 basic inventory is product-level and supports `in_stock`, `low_stock`,
`backordered`, `unavailable`, and `not_tracked`. Quantity reserved may never
exceed quantity on hand.

Variant-level inventory already exists in the domain model and can be surfaced
when authoritative variant data is loaded.

## Customer Inbox and communications archive

Customer Inbox is the commissioned employee-facing correspondence surface.

The PostgreSQL `communication_*` tables are the authoritative durable archive
for customer/company correspondence. `email_deliveries` remains a transport and
delivery-status ledger rather than the message-body archive.

Current behavior includes:

- Inbox / Archived / All views;
- archive/restore without deleting durable communication records;
- manual refresh plus 60-second polling while Operations is open;
- independent scrolling for the conversation list and selected message pane;
- thread-aware replies through Postmark;
- original website request content shown separately from later correspondence;
- quoted reply history may be collapsed in the UI while the full archived body
  remains stored;
- explicit `http://` and `https://` URLs in archived plain text are safely
  linkified while arbitrary inbound HTML is not executed.

Outbound employee replies use approved company sender roles. Quote-request
replies prefer `sales`, then `contact`, `info`, `support`, and `no-reply`.
Other replies prefer `support`, then `contact`, `info`, `sales`, and
`no-reply`. The authenticated staff identity remains the internal author/audit
actor regardless of the selected visible company sender.

Outbound To input accepts comma- or semicolon-separated addresses, normalizes,
deduplicates, and validates them server-side, allows at most 10 recipients, and
archives each recipient separately. CC/BCC composition remains deferred.

## Appearance controls

The site default is Light with the Lagoon Editorial theme. Operations responds
to the shared appearance/font selections and also preserves the user's
light/dark preference.

## Audit

Operations actions emit audit events for sensitive or material state changes,
including quote status, pricing/inventory, and identity-role changes.

Audit Log visibility is developer-only.

## Formal quote governance

Formal quotes are a distinct commercial layer between a customer request and a
future paid order. A `QuoteRequest` records the inquiry/qualification context;
a formal quote records exactly what D'Acqua Dolce offered commercially.

PT19.2 uses immutable quote revisions rather than editing an already presented
quote in place. Each revision snapshots:

- catalog product/variant identity and SKU/name;
- quantity;
- quoted unit amount and line total;
- currency;
- pricing-policy mode at quote creation time;
- applicable estimated lead time when recorded in inventory; and
- an optional customer-facing note.

A draft is private to Operations. Presentation requires a customer account tied
to the request email; only then does the revision become visible in the customer
account. Customer approval records the approving user and timestamp against that
exact revision. Payment and order creation remain separate downstream actions.

Pricing authorization remains server-side. If a current authoritative catalog
amount exists, ordinary Operations staff may use that amount but may not replace
it with a different amount. Administrator/developer authorization is required
for a true catalog-price override. When a product intentionally has no catalog
amount because it is private-quote/no-online-price, employee-entered quote
pricing is allowed and becomes part of the immutable commercial snapshot.

## PT21 fulfillment governance

Payment state and physical fulfillment state are separate concerns. New
quote-origin orders remain in the authoritative payment state `paid` after a
verified successful payment while a separate fulfillment state advances through:

1. `not_started`
2. `supplier_ordered`
3. `received_ready`
4. `shipped`
5. `delivered`

The existing `OrderStatus` values such as `processing`, `shipped`, and
`delivered` remain for backward compatibility with historical order machinery;
PT21 does not use those values as the new fulfillment workflow.

Fulfillment is manual-first. Operations staff record the supplier order step,
may retain an internal supplier order reference, mark equipment received/ready,
and then record carrier + tracking number when the order ships. An optional
tracking URL must use HTTPS. Customer-facing order views never expose the
supplier order reference.

Estimated lead time is copied from the immutable formal-quote line into the
order-item snapshot. This prevents later catalog inventory edits from silently
rewriting what the customer was told at quote time.

Shipment tracking becomes customer-visible only after a shipment record exists.
PT21 supports one shipment record per order. Partial/multi-shipment behavior and
manufacturer API/EDI automation remain deliberately unimplemented until actual
business/provider requirements justify them.

Fulfillment transitions are forward-only and require the order to remain in the
`paid` payment state. Each transition is audited. Cancellation/refund policy
remains separate from fulfillment and must not be inferred from this workflow.

## Consumable relationship governance

A catalog relationship may be marked as a consumable/replacement item independently of its option/accessory classification. This keeps compatibility modeling separate from post-purchase service behavior.

`replacement_interval_days` is intentionally optional. Staff must not populate an interval from generic assumptions; record one only when D'Acqua Dolce has product/manufacturer-supported guidance. A consumable without a supported interval can still be surfaced for reorder without generating a date target.

Making a consumable relationship public controls whether it can appear in the signed-in customer's installed-equipment view. Online reorder remains subject to the related product's own sale approval and pricing policy.

## PT22.2 reminder and calendar governance

Automated replacement reminders must remain opt-in. A consumable relationship may
be associated with one existing reminder preference only when D'Acqua Dolce has
also recorded a supported replacement interval. The supported bindings are
filter replacement, UV service, and product-specific reminders. The application
must not infer a reminder category from product names, SKUs, or marketing copy.

The due-reminder runner is read-only unless explicitly invoked with `--send`.
Live sending additionally requires the commissioned Postmark provider and token.
Every attempted send uses the existing email delivery/archive boundary and a
durable maintenance-reminder business key consisting of installed equipment,
replacement product, reminder kind, and due date. A successful or deliberately
suppressed business key is not resent.

Failed delivery attempts may be retried for the same business key. No payment,
supplier, or private Operations metadata belongs in reminder content.

Calendar integration is intentionally customer-controlled. The account may
generate an all-day `.ics` file for a recorded service target or supported
consumable replacement target. Calendar export is a download only: it does not
request calendar OAuth, write to an external calendar account, or create a
background calendar dependency.

A production schedule for the reminder runner is not implied by application
code. The send window and production timer must be reviewed explicitly during
deployment/commissioning.

## PT23 inventory provenance and assisted-sales intelligence

The existing `product_inventory` row remains the single authoritative inventory
record. PT23 does not introduce a parallel supplier-inventory table and does not
assume any manufacturer API, EDI format, refresh cadence, or credential model.

Each inventory update now records internal provenance alongside the existing
status, quantity, and estimated lead time:

- `unspecified` preserves legacy/unknown provenance without inventing a source;
- `operator_entry` for an operator-entered observation without a more specific
  external source;
- `supplier_report` when the information came from a supplier;
- `manufacturer_report` when it came from a manufacturer; and
- `internal_stock` for future locally held inventory.

An optional internal source reference may identify the portal, report, rep, or
other evidence used. It is Operations-only and must never be exposed to
customers. `source_observed_at` records when the authoritative observation was
entered/checked. Future provider adapters should normalize provider data into the
same inventory-observation service rather than bypassing catalog governance.

Inventory writes require administrator/developer pricing-and-inventory write
authority. Employee access remains read-only. Customer-facing availability
continues to expose only the normalized availability state and supported
estimated lead time, never internal provenance.

Assisted-sales intelligence is observational reporting over the structured
customer-request data already collected. Current aggregates include source-water
mix, treatment-preference mix, top service ZIPs, limited-utility requests,
third-party-lab-review requirements, known hardness values, and the optional
filtration-network research signal.

These aggregates do not modify recommendation decisions, scoring, quote prices,
or self-service eligibility. The optional filtration-network signal remains
research/marketing context and is not part of technical suitability logic.

## PT24.1 commercial quote and order snapshots

Formal quote revisions are the customer-visible commercial source of truth. A new
revision now preserves four distinct layers rather than treating the product-line
subtotal as the entire sale:

1. immutable product/variant line-item snapshots;
2. an explicit product subtotal;
3. zero or more signed commercial adjustments; and
4. the final commercial total.

Supported adjustment categories are shipping/delivery, tax, installation,
discount, other charge, and other credit. Charges are positive; discounts and
credits are negative. Operations must enter the amount explicitly. The
application does not calculate tax, freight, installation pricing, or discount
eligibility in PT24.1.

The final total must equal product subtotal plus the signed adjustment total and
must not be negative. Database constraints preserve the same invariant on both
formal quotes and orders. The hosted-payment boundary continues to use the order
`total_amount_minor`, so a provider adapter cannot accidentally charge only the
product subtotal once PT24.1 is deployed.

Every newly authored formal quote also includes an immutable delivery/service
address snapshot and billing address snapshot. These are commercial-record
snapshots, not live references to the customer's mutable address book. When the
customer approves a quote, both snapshots are copied to the authoritative order.
Changing an account address later must not rewrite what was approved.

Legacy records are preserved conservatively during migration. Existing quote
totals become their product subtotal with zero adjustments; existing order
subtotals become their prior total with zero adjustments. No historical address
is inferred or backfilled from current customer data.

Deposits and partial-payment schedules remain outside this model. The current
payment state machine treats a successful provider event for the exact order
total as payment completion. A future deposit workflow therefore requires a
separate payment-schedule/remaining-balance design rather than overloading a
commercial adjustment or silently marking a partially paid order as paid.

## PT24.2 launch-policy governance

Customer-facing policy text is versioned application data, not hard-coded launch copy.
Policy versions move through explicit `draft`, `approved`, and `retired` states.
Draft policy text remains Operations-only and is never returned by the public policy
endpoint.

Only administrator/developer roles may create or approve policy versions. Approving
a new version retires the previously approved version for that policy kind. Public
policy pages expose only the current approved version.

Newly presented formal quotes snapshot the exact approved policy text, version,
effective timestamp, and SHA-256 digest that apply at presentation time. The baseline
commercial policy set is Terms, Shipping, Cancellation, Refund, and Warranty.
Installation Terms are additionally required only when the quote contains an
installation charge. Privacy remains a separate public-launch policy and is not
treated as a commercial quote term.

A formal quote cannot be presented while an applicable required policy lacks an
approved version. Customer approval must acknowledge the exact policy snapshots
attached to the presented quote. The approval audit event retains the policy kind,
version, and content digest without relying on whatever version may be current later.

This architecture does not make draft language legally sufficient and does not
constitute legal approval. Final policy text must still be reviewed and explicitly
approved by the business and appropriate legal counsel before production workflows
that depend on it are commissioned.
