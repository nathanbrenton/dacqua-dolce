# PT39 — Pricing Governance and Promotional Price Windows

## Purpose

PT39 implements the next launch-safe portion of the client's pricing direction without inventing manufacturer rules, customer discount programs, tax logic, or payment-provider behavior.

The existing architecture already provides:

- authoritative product-level pricing in PostgreSQL;
- `PUBLIC`, `MAP_LIMITED`, `CART_ONLY`, `PRIVATE_QUOTE`, `LOGIN_REQUIRED`, `NO_ONLINE_PRICE`, and `NO_ONLINE_SALE` policies;
- employee read-only Pricing & Inventory access;
- administrator/developer pricing mutation authority;
- employee-entered formal-quote pricing when no authoritative catalog amount exists; and
- administrator/developer authorization for true catalog-price overrides in a formal quote.

PT39 preserves those boundaries and adds conservative temporary promotional pricing.

## Standard pricing

The open-ended active product-level `ProductPrice` row is the standard price. Updating standard pricing closes only the prior open-ended standard row. It does not cancel a separately scheduled temporary promotion.

Historical rows remain preserved rather than overwritten.

## Temporary promotions

A promotion is represented with the existing `ProductPrice` effective-window fields. No database migration is required.

A promotional record:

- is product-level for the initial implementation;
- has a required positive amount;
- has explicit timezone-aware start and end timestamps;
- has a finite `effective_until`;
- inherits the standard price's currency and pricing-policy mode;
- must be lower than the standard price;
- cannot overlap another active/scheduled promotion for the same product; and
- can be cancelled by an administrator/developer without deleting its historical row.

While a promotion is effective, it takes precedence over the open-ended standard price. When it expires or is cancelled, the standard price becomes effective again automatically.

## Conservative policy boundaries

Scheduled promotions are enabled only for these standard policy modes:

- `PUBLIC`
- `CART_ONLY`
- `LOGIN_REQUIRED`

`MAP_LIMITED` promotions are intentionally blocked by this workflow until D'Acqua Dolce has verified manufacturer promotional/MAP terms. PT39 does not infer a permissible advertised discount or manufacture a MAP floor.

`PRIVATE_QUOTE`, `NO_ONLINE_PRICE`, and `NO_ONLINE_SALE` also do not expose scheduled catalog promotions.

## Customer-specific pricing

PT39 does not create an automatic account-wide customer discount engine.

The current manual-first customer-specific mechanism remains the formal quote:

- products with no authoritative catalog amount may be quoted by ordinary Operations staff; and
- overriding an existing authoritative catalog amount remains restricted to administrator/developer authorization.

This keeps launch pricing explicit and reviewable while preserving a path to a future durable customer-pricing model if actual business requirements justify one.

## Operations UI

Pricing & Inventory now distinguishes:

- standard pricing;
- the effective price currently seen by commerce logic; and
- active/upcoming temporary promotions.

Authorized users can schedule or cancel a promotion. Employees retain read-only access.

All PT39 promotion styling remains scoped to the Operations shell.

## Public copy follow-up

The previously approved Service heading copy change is bundled into PT39:

`Support throughout ownership.` → `Support for your system.`

No broader customer typography changes are part of this milestone.

## Deferred

PT39 does not implement or infer:

- manufacturer-specific MAP amounts or promotional exceptions;
- customer-group/account-wide automatic discount schedules;
- coupons or promotion codes;
- tax calculations;
- shipping/delivery calculations;
- Affinity24 integration;
- deposits/partial payments; or
- automatic stock-notification sending.

## Operations disclosure navigation refinement

PT39 also keeps the growing Operations workspace compact by presenting each major operational area as a collapsed disclosure row by default. Commercial launch readiness, assisted-sales insights, launch policies, delivery issues, customer communications, customer requests, customer orders, pricing and inventory, accounts and address book, user access and roles, and the audit log all use the same twirl-down interaction vocabulary.

The overview metrics and next-action card remain visible. When an overview control targets content inside a collapsed section, the application opens the relevant disclosure before scrolling to the requested content. This preserves the existing quick-navigation behavior while preventing the Operations page from becoming excessively long by default.
