# PT40 — Inventory Lifecycle + Availability Enforcement

PT40 separates permanent product lifecycle from temporary stock availability.

## Product lifecycle

- `active`: normal lifecycle.
- `soon_discontinued`: still potentially sellable while stock/fulfillment remains available.
- `discontinued`: no normal purchase or formal quote. This is not presented as merely “Out of stock.”

The existing `products.active` flag remains the catalog publication/record-active boundary. Lifecycle is a separate commercial state so discontinued records can be retained rather than deleted.

## Temporary availability

Existing inventory states remain authoritative for stock (`in_stock`, `low_stock`, `backordered`, `unavailable`, `not_tracked`). PT40 adds a structured `expected_available_on` date while preserving the existing free-text lead-time field as a fallback range. Operations must enter an expected date when known; otherwise it may enter a range such as `2–3 weeks`. The API rejects supplying both.

## Customer behavior

- Out of stock remains a temporary state and can collect Notify When in Stock subscriptions.
- Discontinued is a separate lifecycle state and does not collect back-in-stock subscriptions.
- Customer inquiry remains allowed by default while a product is unavailable.
- Operations can disable inquiry per product when appropriate.
- Soon-to-be-discontinued products can remain purchasable/quotable while actually available.

## Formal quote guardrail

Formal quote creation is blocked by default when a product is effectively out of stock or discontinued. Administrators/developers may explicitly enable a per-product exception only when staff has confirmed that fulfillment remains possible. This does not change the authoritative catalog price-override rules.

## Permissions

PT40 continues using the existing administrator/developer Pricing & Inventory write boundary. The client requested a future inventory-specific permission; PT40 keeps the availability policy isolated so that permission can be introduced later without redesigning these data fields.

## Deferred

PT40 does not send back-in-stock email. Automated delivery remains a later milestone after transition/idempotency and customer unsubscribe behavior are commissioned. PT40 also does not infer supplier quantities or discontinued status from stock counts.
