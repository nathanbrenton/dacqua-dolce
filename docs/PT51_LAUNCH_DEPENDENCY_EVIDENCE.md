# PT51 — Launch Dependency Evidence Registry

## Purpose

PT51 adds an internal commissioning/evidence registry beside the existing PT46
Commerce Launch Gate.

The registry gives Operations a durable place to record progress, source
references, received dates, and internal notes while D’Acqua Dolce waits on
external launch dependencies.

## Tracked dependencies

PT51 tracks these fixed workstreams:

- Automated tax
- Payment / Affinity24
- Legal review
- Shipping insurance
- Public support phone
- Installer program

The registry is intentionally separate from the computed launch-readiness
checks. It does not infer that any external requirement has actually been
satisfied.

## Tracking statuses

Each dependency can use one internal workflow status:

- `Action required`
- `In progress`
- `Evidence received`
- `Evidence verified`
- `Blocked`

These are evidence/workflow labels only.

**No tracking status opens checkout.** In particular, setting a dependency to
`Evidence verified` does not change `DACQUA_LAUNCH_PHASE`, does not change
`commerce_checkout_allowed`, and does not bypass automated-tax, payment,
sales-area, order, cancellation, or other service-level guards.

## Evidence fields

Each dependency may record:

- non-secret source/reference text;
- evidence-received timestamp;
- internal notes;
- creating/updating staff provenance;
- created/updated timestamps.

Do not place passwords, API keys, gateway credentials, merchant secrets, tax
account numbers, or other sensitive credentials in this registry. Production
secrets remain in their established secret/configuration boundary.

## Authorization

- Existing Operations roles may read the registry.
- Administrator and Developer may create/update evidence records.
- Employee and legacy Manager remain read-only for this registry.
- There is no customer/public endpoint.

Updates are audited without copying source text or internal notes into audit
metadata.

## Commerce-gate boundary

PT46 remains authoritative for the aggregate Commerce Launch Gate, while the
underlying service-level checks remain the final enforcement boundary.

PT51 intentionally does not modify `build_launch_readiness()` or checkout
orchestration. It supplies human workflow evidence only. Therefore a manually
updated PT51 record can never turn an unresolved technical or compliance
dependency into a launch-ready condition.

## Deferred

PT51 does not:

- commission Stripe Tax production mode;
- assign or validate tax registrations;
- choose or implement an Affinity24 gateway;
- approve legal language;
- activate shipping insurance;
- publish a support phone number;
- publish an installer directory or claim installer approval.
