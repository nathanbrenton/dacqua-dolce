# PT32 — Formal Quote Cost Breakdown & Taxability Infrastructure

## Purpose

PT32 makes the launch quote cost presentation explicit without creating a tax
engine, carrier-rating engine, insurance product, or duplicate stored totals.

The customer-facing headline breakdown is:

1. Product / Other Costs
2. Shipping / Delivery Cost
3. Shipping Insurance
4. Tax Cost
5. Total Cost

The same canonical breakdown is returned to Operations and Customer Account
views.

## Canonical source of truth

PT32 does **not** add four new persisted subtotal columns. The existing formal
quote remains authoritative:

- product line snapshots determine the product subtotal;
- typed commercial adjustments remain immutable with the quote revision;
- `charges_amount_minor` remains the sum of commercial adjustments;
- `total_amount_minor` remains the stored final total.

`commercial_cost_breakdown()` derives the four presentation buckets and verifies
that their sum equals the stored final total.

This avoids duplicated financial state that could drift after a quote is
presented.

## Bucket mapping

`Product / Other Costs` is the net of:

- product subtotal;
- installation charges;
- other charges;
- discounts;
- other credits.

`Shipping / Delivery Cost` contains `shipping` adjustments.

`Shipping Insurance` contains the new `shipping_insurance` adjustment kind.

`Tax Cost` contains `tax` adjustments.

All individual commercial adjustments remain available so employees and
customers can still see the underlying labels and amounts.

## Shipping insurance boundary

PT32 only establishes a distinct commercial line type and presentation bucket.
It does not define or imply:

- an insurance provider;
- policy coverage;
- risk-of-loss terms;
- claim handling;
- customer acceptance/refusal mechanics;
- licensing or regulatory status;
- automatic premium calculation.

Those remain pending provider/legal/business decisions.

## Tax boundary

PT32 does not encode the earlier business assumption that tax applies only to
products. Taxability can vary by jurisdiction and transaction facts.

Employees may enter an explicit tax amount on a quote, but the application does
not determine:

- taxable products or services;
- taxable shipping;
- taxable insurance;
- jurisdiction;
- nexus;
- exemptions;
- tax rate.

A future tax integration or reviewed ruleset must own those decisions.

## Order preservation

The existing approved-quote-to-order workflow copies every commercial
adjustment exactly. PT32 expands both quote and order charge constraints to
accept `shipping_insurance`, so an approved quote preserves the insurance line
when materialized as an order.

No Affinity24 settlement behavior is added.

## Historical quotes

Historical quotes require no backfill. If no `shipping_insurance` adjustment is
present, the derived Shipping Insurance bucket is zero.

## Migration

Alembic revision `d4f8c2a71b30` expands the existing formal-quote and order
charge-kind/sign constraints to admit positive `shipping_insurance` rows. It
does not alter historical financial values.
