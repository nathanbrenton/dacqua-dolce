# PT44 — Automated Tax Foundation

## Purpose

PT44 establishes the application boundary required for authoritative automated
sales-tax calculation before online checkout. It does **not** activate live tax
collection.

The implementation is provider-neutral internally. The first adapter is Stripe
Tax in test mode, used only as a tax engine; Affinity24 remains the intended
payment provider.

## Safety boundary

PT44 accepts only:

- `DACQUA_TAX_PROVIDER=disabled`; or
- `DACQUA_TAX_PROVIDER=stripe_test` with a Stripe test/restricted-test secret.

Live Stripe credentials and a `stripe_live` mode are rejected by design. No
Stripe credential is exposed to the frontend, audit metadata, or stored tax
evidence.

The application does not infer product taxability. Every product used in an
automated calculation must have an active Stripe Tax product tax code plus the
authoritative source used to classify it. Operations Administrator/Developer
users manage that evidence through Pricing & Inventory.

## Evidence model

PT44 adds three durable records:

1. `product_tax_classifications`
   - product;
   - provider;
   - exact provider tax code;
   - source/reference;
   - verifier and verification timestamp;
   - active state.

2. `tax_calculations`
   - exactly one formal-quote or order context;
   - provider calculation identifier;
   - currency;
   - merchandise, shipping, tax, and total amounts;
   - test/live indicator;
   - provider expiry;
   - sanitized request and response summaries;
   - supersession and transaction-commit state.

3. `tax_transactions`
   - one order and one authoritative calculation;
   - provider transaction identifier/reference;
   - currency, tax, and total evidence;
   - sanitized provider summary.

Raw provider responses and credentials are intentionally not stored.

## Calculation boundary

### Draft formal quote

A privileged Operations user may request a sandbox tax calculation for a
**draft** formal quote.

The calculation:

- requires a delivery address;
- requires an explicit sourced product tax classification for every product
  line;
- treats D’Acqua Dolce prices as tax-exclusive;
- sends shipping/delivery as a separate provider shipping amount;
- replaces any existing tax charge on that draft;
- reconciles provider merchandise, shipping, tax, and total amounts before
  saving;
- supersedes prior uncommitted calculations for the same quote.

The formal quote remains the historical quote context. A quote tax calculation
is not reused as the final checkout tax calculation.

### Awaiting-payment order

The order receives a separate tax recalculation before checkout. This is
intentional: tax evidence can expire or change between quote creation and
payment.

The order calculation updates only the tax charge and authoritative total,
leaving the source formal quote unchanged.

## Unsupported commercial adjustments

PT44 intentionally refuses automated tax calculation when a quote/order contains
a charge whose tax treatment has not yet been explicitly modeled:

- shipping insurance;
- installation;
- discount;
- other charge;
- other credit.

Shipping/delivery is supported separately. This fail-closed boundary prevents
the application from silently guessing jurisdiction-specific taxability.

## Checkout boundary

Provider-neutral hosted checkout now requires a current authoritative order tax
calculation whose:

- amount and currency exactly match the order;
- provider evidence is not expired;
- evidence has not already been committed to a tax transaction;
- evidence is test-mode under PT44.

Missing, stale, or mismatched tax evidence blocks checkout.

Because PT44 is sandbox-only, this deliberately means production checkout
remains blocked until the later live-tax commissioning milestone.

## Post-payment transaction boundary

PT44 includes a service that can create a Stripe Tax transaction from the exact
order calculation after verified payment.

It is **not** automatically wired into payment-provider events yet. That wiring
must wait for the authoritative Affinity24 integration contract so payment
success, retries, refunds, and tax transaction/reversal behavior can be
coordinated correctly and idempotently.

## Sales territory versus tax registration

The PT35 sales territory remains a separate policy from tax registration.
Being allowed to ship to a state does not itself mean D’Acqua Dolce is
registered to collect tax there.

Live Stripe Tax registrations, nexus/compliance decisions, filing setup, and
account commissioning remain external launch requirements.

## Operations and launch readiness

Operations exposes each product's recorded tax classification and provenance.
No product is seeded with or assigned a default tax code.

Commercial Launch Readiness now treats automated tax as **Action required**
rather than Deferred. It reports tax-classification coverage while explicitly
stating that PT44 is test-mode only and production tax registrations/live
commissioning remain incomplete.

## Configuration

Local/test sandbox example:

```text
DACQUA_TAX_PROVIDER=stripe_test
STRIPE_TAX_SECRET_KEY=<Stripe test-mode or restricted-test key>
```

Default:

```text
DACQUA_TAX_PROVIDER=disabled
```

No live mode exists in PT44.

## Migration

PT44 adds Alembic revision:

`b7e0c9d31a42` — `add automated tax foundation`

It follows `a6d4f8c21b90`.

## Deferred to later commissioning

PT44 does not:

- select or configure live tax registrations;
- provide tax/legal/accounting advice;
- infer tax codes;
- activate live Stripe Tax credentials;
- replace Affinity24 for payments;
- wire successful Affinity24 payments to tax transactions;
- implement tax reversals/refunds;
- decide taxability for shipping insurance, discounts, installation, or custom
  charges;
- enable production checkout.
