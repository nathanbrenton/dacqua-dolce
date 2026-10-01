# PT27 — Launch Assisted-Sales Boundary and Quote Validity

## Implemented decisions

- Whole-house systems require employee review before purchase at initial launch.
- Non-whole-house products do not require employee review solely because of product class.
- Manufacturer/component online-sale approval and pricing policy remain separate gates.
- Formal quotes presented after this milestone are valid for 30 days from presentation.
- Existing historical quote rows with no expiration are grandfathered rather than retroactively expired.

## Canonical catalog mapping

- Harmony and Essence whole-house products: assisted sale required.
- Origin point-of-use reverse-osmosis products: assisted sale not required.
- The retired Harmony record remains assisted-sale-required if ever reactivated.

## Intentionally deferred

The following client answers are not hard-coded in PT27 because they still require a
final business, provider, manufacturer, geographic-definition, or legal decision:

- exact definition of the Continental United States sales area;
- 60-day versus case-by-case return approval;
- 25% versus case-by-case restocking fee;
- post-supplier-confirmation cancellation matrix;
- shipment-insurance offering, acknowledgement, and risk-of-loss mechanics;
- manufacturer-specific warranty terms;
- Affinity24 gateway/API implementation.

The existing Draft / Approved / Retired policy workflow remains the publication gate
for customer-facing policies.
