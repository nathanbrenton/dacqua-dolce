# PT53 — Policy Portability + Environment Sync

PT53 adds explicit, manual portability for D’Acqua Dolce customer policy versions without copying the production database.

## Authority model

- Git remains authoritative for application code, schema, and behavior.
- Production PostgreSQL remains authoritative for live approved policy versions.
- Policy bundles are transport artifacts, not a new source of truth.
- Imports never delete destination-only policy versions.
- Existing formal-quote policy snapshots are not modified by import.

## Export

Operations users can export either:

- **All policy versions** — Draft, Approved, and Retired history.
- **Approved/effective only** — the currently approved version for each policy kind.

The JSON bundle contains policy kind/version, title/body, structured terms, lifecycle/effective timestamps, source-created time, and SHA-256 integrity hashes. It excludes customer data, credentials, secrets, and source-environment user IDs.

## Import preview

Administrator/Developer users load a bundle and preview it before applying. Each policy version is classified as:

- `add` — missing from the destination;
- `skip` — matching content already exists;
- `conflict` — same policy kind/version exists with different content;
- `update_lifecycle` — matching content needs lifecycle synchronization in non-production mirror mode;
- `retire_destination_approved` — a destination-only approved version must be retired so the incoming approved version can be mirrored.

Any content conflict blocks apply. Bundle and per-policy hashes are validated before preview or apply.

## Safe import mode

`draft_only` is the default and production-safe mode. Missing versions are created as Draft regardless of their source lifecycle status. Existing matching versions are skipped; conflicting versions are never overwritten.

This permits a deliberately reviewed Local/Dev/Test-to-Production transfer without silently publishing imported text. Normal policy approval remains required in Production.

## Non-production mirror mode

`preserve_lifecycle` is intended for periodically synchronizing Local/Dev/Test from Production so test environments can reproduce the real approved/retired policy state.

It is disabled unless the destination runtime explicitly sets:

`DACQUA_POLICY_IMPORT_ALLOW_LIFECYCLE_PRESERVATION=true`

Do not enable this flag in Production.

When enabled, matching policy content can synchronize Draft/Approved/Retired status and effective/approval timestamps. If the source bundle has a different approved version for a policy kind, the destination's previous approved version is retired rather than deleted.

## Recommended quarterly flow

1. In Production Operations, export **All policy versions**.
2. Store/transfer the JSON bundle through the normal trusted administrative workflow.
3. In Local/Dev/Test, enable lifecycle-preserving import for that environment.
4. Load the Production bundle.
5. Preview the import.
6. Resolve any content conflicts rather than overwriting them.
7. Apply only after the preview is understood.
8. Re-run preview if desired; a repeated import should be idempotent and report matching versions as skipped.

## Security / privacy boundary

Policy portability is intentionally narrower than database synchronization. It does not export or import customers, accounts, addresses, quotes, orders, communications, payment/tax evidence, credentials, secrets, or unrelated audit history.
