# D'Acqua Dolce — Operations and Pricing Governance

## Purpose

The Operations Console keeps operational business decisions on the authenticated
server side instead of hard-coding them into the customer frontend.

The console currently covers:

- quote-request queue and status;
- product-level pricing policy;
- product-level basic inventory;
- dashboard counts for quote/catalog/email operations.

## Role boundary

Quote and inventory operations:

- employee
- manager
- administrator
- developer

Pricing-policy changes:

- manager
- administrator
- developer

Customer accounts do not receive operations access.

Frontend role visibility is convenience only. Every operations endpoint
independently enforces roles in FastAPI.

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

- PUBLIC
- MAP_LIMITED
- CART_ONLY
- LOGIN_REQUIRED

Restricted modes deliberately reject a stored online amount:

- PRIVATE_QUOTE
- NO_ONLINE_PRICE
- NO_ONLINE_SALE

This prevents the console from becoming a workaround for a manufacturer rule
that prohibits online price display or online sale.

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

## Audit

Operations actions emit audit events for quote status changes, pricing-policy
changes, and inventory changes.
