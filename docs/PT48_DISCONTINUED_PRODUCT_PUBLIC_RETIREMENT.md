# PT48 — Discontinued Product Public Retirement

PT48 extends the PT40 product lifecycle without deleting catalog/history records.

## Behavior

- `Discontinued` remains distinct from temporary out-of-stock state.
- A discontinued product remains public by default.
- Administrators/Developers may set an explicit timezone-aware `public_retire_at`.
- Before that timestamp, the discontinued product remains visible and clearly
  labeled `Discontinued`.
- At/after that timestamp, the product is omitted from public catalog listing,
  product detail, availability, and new stock-notification subscription routes.
- Operations/internal history remains available; PT48 performs no product deletion.
- No default retirement duration is hard-coded.

## Replacement/current product recommendations

PT48 adds an explicit `replacement` product relationship type. Relationships start
internal. Staff must deliberately mark a verified relationship public before it is
customer-visible.

A public replacement recommendation is shown only when:
- the relationship is active and public;
- the related product remains active/publicly visible; and
- the related product itself is not discontinued.

## Authorization and audit

The existing Pricing & Inventory write boundary remains unchanged:
Administrator/Developer only. Availability-policy changes continue through the
existing audited endpoint, now recording `public_retire_at` as evidence.

## Migration

Revision `c8f1d2e43b57` follows `b7e0c9d31a42`.
