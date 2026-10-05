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

PT45 supersedes PT34's original `Deferred` status. Payment & checkout is now
an `Action required` launch dependency. The provider-neutral commissioning
contract is implemented, while the exact Affinity24-provisioned gateway,
authoritative integration contract, credentials, authenticated webhook details,
and explicit production commissioning remain unresolved.

### Tax handling

PT44 supersedes PT34's original `Deferred` tax status. Automated tax is now an
`Action required` launch dependency.

The application has a provider-neutral evidence model and a Stripe Tax
**test-mode-only** adapter. Every commercial product must have an explicitly
reviewed, sourced provider tax classification before it can participate in an
automated calculation. Live credentials are rejected by design in PT44.

Hosted checkout fails closed without a current authoritative order tax
calculation. Production tax registrations, live credentials, filing/account
commissioning, and Affinity24 post-payment coordination remain incomplete, so
the tax check cannot report `Ready` under PT44.

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

PT46 adds the Commerce Launch Gate to this view. The page now reports the
deployment launch phase and aggregate blocker state. Checkout itself remains
enforced by service-level guards; the Operations readiness view cannot bypass
those guards.

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

## PT46 refinement

Launch posture is now explicit through `DACQUA_LAUNCH_PHASE`, which defaults to
`prelaunch`. `soft_launch` supports invited/test validation while keeping
transactional checkout closed. Only `public_launch` permits checkout to proceed
to the independent sales-area, tax, payment-provider, order, and cancellation
guards. The readiness response surfaces this Commerce Launch Gate and its
current blockers.
