# Product family ordering and shared notifications

**State:** locally implemented and browser-reviewed; **not yet deployed to production** at time of writing. Backend test suite: **539 passed**, as reported by local operator. Frontend build reported successful. Toast visual uniformity across themes/fonts is **deferred**. Do not mark this feature production-commissioned until deployment and production acceptance.

## System of record

Product-family display sequence is mutable **PostgreSQL state**, not a frontend constant or a Git-managed catalog preference. The Alembic revision `c1e4f9b73a62` (parent `b32e10c7a9d4`) creates `product_family_order` with one row (`id=1`), positive integer `revision`, and `families_json` (JSON-encoded text). The original migration seeds revision `1` with `["Refine", "Essence", "Origin", "Harmony"]`; follow-up revision `d921ae0c7254` updates only an untouched revision-1 seed to `["Refine", "Essence", "Harmony", "Origin"]`. Existing revision-2+ staff preferences remain unchanged. Reapplying ordinary deployments does not reset a saved order.

The backend helper `backend/app/services/product_family_order.py` derives family identity from `product_family` (falling back to product name), computes active family names from existing product records, merges new/unlisted families into the effective sequence, and sorts public catalog results first by saved family position, then family/name/id as deterministic tie-breakers. The saved family order does **not** change product pricing, lifecycle, inventory, order records, or variant groupings. Families outside the default four may be present and should be explicitly reviewed after catalog updates.

## Staff workflow and authorization

Open the authenticated **Operations > Pricing & Inventory > Product display order** panel. Use Up/Down controls, then **Save order** to persist; **Cancel** discards unsaved edits; **Restore default** prepares the recommended initial family order, but it is **not persisted until Save order**. Reload the Operations panel after another operator changes the order. Do not rely on a transient UI state as evidence of persistence: refresh the page and verify the public catalog.

`GET /api/operations/catalog/family-order` requires an authenticated Operations user; `PUT /api/operations/catalog/family-order` invokes the existing pricing/inventory write guard for privileged staff (intended Admin/Developer). The PUT requires **every currently available family exactly once** and the last-read integer revision. It acquires a database row lock, rejects unknown/missing/duplicate families (`422`) and stale revision (`409`), commits the updated order/revision, and records an audit event `catalog.family_order_changed` with previous/new order, revision, and actor. The client must reload after a `409` rather than overwrite the other operator's change. The public `GET /api/catalog/products` reads the stored order for display. These routes are application code, not dashboard configuration.

## Shared toast system — source and known limitation

`frontend/src/components/toast/ToastProvider.tsx` supplies a root-level notification context. Its `useToast()` API supports `success`, `info`, `warning`, `error`, plus `show`. Success displays for **4 seconds**, information **5 seconds**, warning **7 seconds**, and errors are persistent by default until dismissed. Three existing floating-notification integrations were moved to this provider: Support Request, Customer Account, and Product Display Order. The toast stack is bottom-right, bounded to four visible items, dismissible via the close control or Escape for the newest toast, with error `role=alert` and other variants `role=status`.

`frontend/src/components/toast/toast.css` uses semantic style tokens such as `--surface-elevated`, `--hairline`, `--ink`, `--font-ui`, `--type-small`, `--success`, `--warning`, `--danger` and responsive/reduced-motion rules. **Known deferred work:** browser review found that visual styling was still not uniform with all existing customer/Operations notifications across themes/font variants. The shared provider exists; do not claim full visual unification or theme-by-theme acceptance. Existing persistent input-level validation and workflow errors appropriately remain inline rather than being converted wholesale into disappearing toasts.

## Local developer verification (macOS — repo root)

Use only the local guarded database migrator. `alembic heads` reports the migration available in code, not the database's applied revision.

```sh
# Confirm actual local database migration revision; no change.
bash scripts/alembic_local.sh current

# Apply to LOCAL guarded dev database only, if it is behind. Changes DB schema.
bash scripts/alembic_local.sh upgrade head

# From repository root: test using the configured local backend virtualenv.
(cd backend && .venv/bin/python3 -m pytest -q --tb=short)

# Frontend compilation (does not replace browser acceptance).
(cd frontend && npm run build)

# Check diffs before committing.
git diff --check
git --no-pager status --short --branch
```

Local browser checks: verify initial sequence Refine > Essence > Harmony > Origin; save a different order, reload and confirm persistence; verify public catalog; restore default and Save; ensure variant details/prices/inventory are unchanged; test unauthenticated and nonprivileged write denial; verify concurrent stale revision produces `409`; inspect notification timing/dismissal on customer Support, Account, and Operations. Record the outstanding CSS harmonization separately.

## Production release and rollback boundary

**Never treat this section as authorization to deploy.** Follow `DEPLOYMENT_AND_ROLLBACK.md`, using the approved exact **40-character Git SHA** and the existing staged immutable-release procedures; never rsync directly into `/srv/dacqua-dolce/current`.

1. Verify local tests/build, source revision, committed migration and docs, and no unintended files. Obtain deployment approval.
2. Stage approved source through `scripts/production/stage_release_rsync.sh`; verify exact revision/source integrity.
3. Take and verify a **pre-migration PostgreSQL backup** using the canonical deployment workflow; record path and timestamp. A backup file alone is not a successful restore test.
4. Apply the migration using production's **migrator** authority; ensure `c1e4f9b73a62` is the new Alembic head. Never run production migrations as the runtime database user.
5. Activate the immutable application release only after required checks; allow bounded Uvicorn readiness retries.
6. Check public catalog, authenticated ordering panel, save/reload behavior, audit event, denial for unprivileged writes, security headers, and other ordinary production smoke tests. Avoid unnecessary actual customer Support submissions/emails.
7. Record active release SHA, backup, actual DB revision, and previous-release rollback target.

An application-only rollback may be possible when old application code ignores the newly added table, but **do not assume** that changing the release symlink reverses the database schema or restores prior ordering. The Alembic `downgrade()` drops the entire `product_family_order` table, deleting saved merchandising state. Do not downgrade production as a routine frontend/application rollback. If DB recovery is required, use the authorized database restore workflow after confirming customer-data implications and separate restore acceptance.

## Clean rebuild, disaster recovery, and future PT33 instances

**Clean rebuild with fresh DB:** normal Alembic chain creates default family order. **Disaster recovery:** restore authorized PostgreSQL mutable state to recover the then-saved order; do not overwrite with seeds or assume Git reproduces the last staff-selected sequence. Check restored row and revision during post-restore validation.

**New business:** future PT33 provisioning should create an independently scoped ordering record in its own database. The present D’Acqua-specific four-family default is not a universal merchandising default. Do not seed D’Acqua products/order in another business unless its explicitly selected business profile requires those families. Shared toast presentation may be reused across businesses, subject to branding/theming adaptation and acceptance.
