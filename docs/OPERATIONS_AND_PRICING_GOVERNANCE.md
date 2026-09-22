# D'Acqua Dolce — Operations, Account Administration, and Pricing Governance

## Purpose

The Operations console keeps operational business decisions on the authenticated server side instead of hard-coding them into the customer frontend.

The current console covers:

1. Customer Requests
2. Customer Orders
3. Pricing & Inventory
4. Accounts & Address Book
5. User Access & Roles
6. Customer Email Activity
7. Audit Log

The disclosure/section order above is intentional and should remain consistent between local and production builds unless a later UX milestone explicitly changes it.

## Role boundary

Quote, order, customer/address, inventory, and ordinary operations access:

- employee
- manager
- administrator
- developer

Pricing-policy changes:

- manager
- administrator
- developer

Account-role administration:

- administrator
- developer

Web-managed account roles are limited to `employee`, `manager`, and `administrator`. The `developer` role is intentionally CLI-managed only. Customer accounts do not receive Operations access merely by registering.

Frontend role visibility is convenience only. Every operations/administration endpoint independently enforces roles in FastAPI.

Privileged roles are subject to the application's MFA policy.

## Account administration safeguards

The web role editor must preserve the `customer` role and must not become a path to edit the `developer` role.

Current safeguards include:

- no self-removal of the active administrator's own administrator role;
- no removal of the final active administrator;
- developer accounts are rejected by the web role editor;
- successful role changes generate audit events.

## Pricing-policy governance

Price values are authoritative database records. Prices must never be embedded in frontend source code, static HTML, CSS, SEO metadata, or generated marketing content.

Supported product-level policy modes:

- `PUBLIC`
- `MAP_LIMITED`
- `CART_ONLY`
- `PRIVATE_QUOTE`
- `LOGIN_REQUIRED`
- `NO_ONLINE_PRICE`
- `NO_ONLINE_SALE`

Modes that support an online transaction or visible authenticated/public price require an authoritative amount:

- PUBLIC
- MAP_LIMITED
- CART_ONLY
- LOGIN_REQUIRED

Restricted modes deliberately reject a stored online amount:

- PRIVATE_QUOTE
- NO_ONLINE_PRICE
- NO_ONLINE_SALE

This prevents the console from becoming a workaround for a manufacturer rule that prohibits online price display or online sale.

## Historical pricing

A pricing change does not overwrite the prior row. The prior active product-level pricing record is closed with `effective_until` and marked inactive, then a new active pricing record is created.

## Inventory

P0 basic inventory is product-level and supports `in_stock`, `low_stock`, `backordered`, `unavailable`, and `not_tracked`. Quantity reserved may never exceed quantity on hand.

Variant-level inventory already exists in the domain model and can be surfaced when authoritative variant data is loaded.

## Customer email activity boundary

The current Operations email activity surface represents delivery metadata such as message category, recipient, provider status/reference, and bounded error details. It is not yet a complete employee shared mailbox or durable body-level correspondence archive.

The planned communications milestone will introduce dedicated PostgreSQL communication/thread/message records and Postmark inbound/outbound integration rather than repurposing `email_deliveries` to store message bodies.

## Appearance controls

Operations keeps its own light/dark appearance toggle and defaults to dark when no preference has been saved.

Authenticated Account pages expose visual-theme selection and an account-page light/dark preference for all account types. Footer-logo appearance controls remain available separately; developer-only logo-artwork controls remain restricted to developer mode.

## Audit

Operations actions emit audit events for sensitive or material state changes, including quote status, pricing-policy, inventory, and account-role changes.
