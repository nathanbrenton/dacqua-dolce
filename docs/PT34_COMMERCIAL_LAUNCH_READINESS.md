# PT34 — Commercial Launch Readiness & Configuration Audit

## Purpose

PT34 adds a read-only Operations snapshot for commercial-launch dependencies.
It does not activate checkout, alter quote behavior, approve policy content, or
make unresolved business decisions.

The snapshot is informational. Existing service-level guards remain
authoritative.

## Readiness checks

### Sales area

The audit reads the existing `DACQUA_SALES_AREA_*` configuration.

- `Ready` means allowlist enforcement is enabled and exactly matches the
  PT35-approved launch territory: the 48 contiguous states plus Washington, DC.
- `Action required` means enforcement is disabled, configuration is invalid, or
  the enabled country/region set drifts from that approved launch policy.

PT34 itself did not choose the region set. PT35 supplied the business decision
and tightened this readiness check so an arbitrary non-empty allowlist cannot
be reported as ready.

### Required policies

The audit checks the five base policy kinds already required before a formal
quote can be presented:

- Terms & Policies
- Shipping Policy
- Cancellation Policy
- Refund Policy
- Warranty

The existing Draft / Approved / Retired workflow remains authoritative.

### Warranty documents

The audit evaluates active products that are explicitly approved for online
sale. Each evaluated product should have at least one warranty document that
satisfies the existing PT31 sale-readiness rule: active, public, verified, and
protected by a valid SHA-256 checksum.

PT34 does not create or approve manufacturer warranty terms.

### Catalog & inventory

The same active online-sale-approved products are checked for at least one
sourced, timestamped availability observation whose inventory status is not
`not_tracked`.

This is an operational signal only. It does not automatically change catalog
availability or purchasing permissions.

### Payment & checkout

Status remains `Deferred`. Provider-neutral hosted-checkout orchestration
exists, but the production Affinity24 gateway/adapter and credentials are not
commissioned in the application.

### Tax handling

Status remains `Deferred`. Formal quotes support a separate tax charge, but
PT34 does not encode nexus, jurisdiction, item taxability, rates, or a tax
engine.

### Shipping insurance terms

Status remains `Deferred`. The quote charge and customer accept/decline
evidence exist, but provider terms, coverage, rating, claims, and legal effect
are still unresolved.

## Operations behavior

`GET /api/operations/launch-readiness` is restricted by the existing Operations
authorization boundary.

The Operations page loads the snapshot with the rest of its read-only overview
data and displays:

- number of checks ready;
- number requiring action;
- number intentionally deferred;
- per-check detail and evidence;
- evaluation timestamp.

The page explicitly states that the audit does not enable or disable checkout.

## Configuration documentation

PT34 originally added the sales-area variables to `backend/.env.example` with
enforcement disabled by default. PT35 supersedes that temporary configuration
with the approved contiguous-U.S.-plus-DC allowlist and documents the exact
production values that must be commissioned.

## No database migration

PT34 derives all status from existing configuration and database records. It
adds no tables, columns, constraints, or data migration.


## PT36 refinement

The Required policies check now also requires the approved Refund Policy to contain valid structured return/restocking terms. The check reports the configured values but does not hard-code the initial 60-day / 15% business decision, so later approved policy versions can change those values without a software release.
