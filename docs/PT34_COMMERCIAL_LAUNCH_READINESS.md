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

- `Ready` means allowlist enforcement is enabled with explicit regions.
- `Action required` means enforcement is disabled or the configuration is
  invalid.

PT34 does not choose the approved region set.

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

PT34 adds the existing sales-area variables to `backend/.env.example` with
enforcement disabled by default. Production values remain an operator decision
and are not changed by this milestone.

## No database migration

PT34 derives all status from existing configuration and database records. It
adds no tables, columns, constraints, or data migration.
