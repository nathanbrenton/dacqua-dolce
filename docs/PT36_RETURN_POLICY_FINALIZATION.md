# PT36 — Return Policy Finalization and Versioned Exceptions

## Business decision

The initial D'Acqua Dolce return-policy configuration is:

- standard return window: **60 days**;
- eligibility mode: fixed window with authorized case-by-case exceptions;
- standard restocking fee: **15%**;
- merchandise condition: new/uninstalled;
- customer normally pays return shipping;
- original outbound shipping normally is not refunded, with the already-recorded
  business-error, defect, or authorized-discretion exception direction.

The 60-day and 15% values are **not application constants**. They belong to the
approved Refund Policy version's `structured_terms`. Changing either value later
requires a new policy version, not a source-code change.

## Existing infrastructure reused

PT28/PT31 already provide:

- Draft / Approved / Retired policy lifecycle;
- approval-time `effective_at`;
- one current approved version per policy kind;
- machine-readable Refund Policy terms;
- immutable formal-quote policy snapshots;
- structured-term SHA-256 evidence;
- customer acknowledgement of quote policy snapshots.

PT36 deliberately reuses those capabilities rather than creating a second policy
configuration table.

## Launch-readiness rule

An approved Refund Policy is no longer sufficient by text alone. Commercial Launch
Readiness requires the approved Refund Policy to contain valid structured return terms.

The readiness check is deliberately **data-driven**. It validates and reports the
currently approved values but does not require 60 days or 15% in source code. If the
business later approves 30 days and 10%, the readiness check remains valid without a
software release.

## Future policy changes

Operations provides **Start successor draft** on an approved policy. This copies the
current title, text, and structured terms into the draft editor. An administrator or
developer can then:

1. assign a new version;
2. update reviewed customer-facing text;
3. change structured return/restocking values;
4. save the new version as Draft;
5. approve it when business/legal review is complete.

Approval retires the previously approved version. Existing formal quotes retain the
old snapshotted text and structured terms.

## Order-specific exceptions

PT36 adds a narrow exception-evidence capability without creating a full RMA or
payment-refund workflow.

Manager, administrator, and developer roles may authorize an exception to a
snapshotted Refund Policy for a specific order. Supported evidence fields are:

- replacement return-window days;
- replacement restocking percentage, including 0% to waive the fee;
- whether the customer or business pays return shipping;
- whether original outbound shipping is refundable;
- required reason.

The authorization is stored as an immutable audit event tied to:

- the order;
- the actor;
- the governing Refund Policy snapshot ID and version;
- the exact override values;
- the reason;
- the audit timestamp/environment/request evidence already supplied by the audit
  subsystem.

This does **not** issue money, change order status, create an RMA, or contact a payment
provider.

## Current activation procedure

After PT36 code is deployed, use Operations -> Launch policies:

1. locate the currently approved Refund Policy;
2. choose **Start successor draft**;
3. set a new version;
4. ensure the customer-facing policy text accurately reflects the reviewed terms;
5. enable structured return settings;
6. select **Fixed window with case-by-case exception**;
7. enter **60** days;
8. select **Fixed percentage**;
9. enter **15** percent;
10. save as Draft;
11. approve only after the required business/legal review is satisfied.

The software does not invent or auto-approve legal wording.


## Draft-save acceptance UX

Browser acceptance found that a successful draft save could be easy to miss because
the existing success/error banner is rendered at the top of the Launch Policies
section while the Save button is far below it. A second click could therefore attempt
to create the same policy version again and surface a duplicate-version error.

PT36 now also:

- shows draft-save success or error feedback immediately below **Save draft version**;
- exposes an in-progress **Saving draft…** state;
- uses a synchronous in-flight guard so a rapid second click cannot submit the same
  draft twice before React re-renders.

The existing top-level policy banner remains available for broader policy actions.

## Explicitly deferred

PT36 does not implement:

- customer-initiated return requests;
- RMA numbers;
- returned-item inspection/disposition;
- partial-return line selection;
- automated restocking-fee calculation;
- automated refunds/voids;
- Affinity24 refund API calls;
- shipping-label purchasing;
- shipping-insurance claims.

Those require later workflow/provider decisions.
