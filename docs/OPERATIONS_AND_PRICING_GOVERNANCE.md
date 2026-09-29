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
