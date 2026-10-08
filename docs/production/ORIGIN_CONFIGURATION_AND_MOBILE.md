# Origin Configuration and Mobile Catalog — Implementation and Release Notes

**Status:** Local candidate, not yet committed or production-deployed. Base Git revision: `3651d78ad414581e08f8908b4a142af6d2996a1f`. Current uncommitted source changes are captured in the Origin final-context audit. Local browser acceptance, backend regression, and frontend build were reported PASS; release validation and production browser acceptance are separate gates.

## User-facing catalog and SKU authority

- Public `/api/catalog/products` skips the `DD5ROAE` card while leaving the product and its direct detail endpoint available. The single visible Origin card represents the **DD5RO** default. Do **not** deactivate or delete `DD5ROAE` from the authoritative catalog merely to remove the duplicate card.
- `DD5RO` and `DD5ROAE` retain separate product IDs, images, specifications, availability, and future commerce identity. The product-detail configuration switch navigates between `/systems/dd5ro` and `/systems/dd5roae` with scroll/focus preservation. A transient fetch keeps previous details visible; successful fetch refreshes the SKU-specific content. Standard page navigation retains its existing scroll/focus behavior.
- The shared identity for both options is **Under-Sink Filtration → Origin → Reverse Osmosis**. Configuration options are **Standard Reverse Osmosis** and **With Alkaline Remineralization**. Customer inquiry and product-linked support headers use **Origin — Standard** or **Origin — Remineralization**. Submission must still contain the actual selected product ID; never replace with a display label.
- The DD5RO canonical description removes the obsolete sentence promoting “Origin Alkaline Plus.” A separate page-level guidance sentence offers the remineralization configuration without unverified performance improvement claims. No unverified price, cartridge compatibility claim, or guaranteed treatment outcome should be introduced.
- Historic `/systems/dd5roae` links must remain valid; browser Back/Forward must restore the correct selected configuration. Tests should specifically check no scroll-to-top when switching and correct image/spec/availability/inquiry data after the asynchronous transition.

## Mobile content and presentation

- The “Recommend a System” primary hero button is centered using flex alignment and centered text.
- Catalog headline: “Better water, designed around your life.”
- Catalog introduction: “Explore our water treatment systems and pricing below.”
- Installation callout: “Installation & Services”; equipment is offered without installation, and future installation services/referrals are described as possibilities, not commitments. This changes copy only, not installation sale/fulfillment policies.
- The Refine selector, Essence/Harmony behavior, public forms, PT32 Turnstile protection, and product ordering are not intentionally modified by this release.

## Source ownership and data integrity

- `backend/app/api/catalog.py` controls the public grid exclusion. Direct product fetching must continue to support both Origin SKUs.
- `backend/catalog/production_catalog.json` is authoritative for the seed-owned DD5RO description. Deployment's canonical catalog reconciliation may update this description in production; a mere frontend rollback will **not** revert this persisted description.
- `frontend/src/components/catalog/productPresentation.ts` owns the shared Origin category/family/descriptor.
- `frontend/src/components/catalog/CatalogSection.tsx` owns the mobile/catalog content. `frontend/src/components/catalog/ProductDetailPage.tsx` owns the configuration selector and derived inquiry/support labels. `frontend/src/App.tsx` manages the opt-in scroll/focus-preserving route behavior. `frontend/src/styles.css` owns button alignment.
- Preserve prices, product IDs, variants, original product image/spec provenance, historical inquiry/order references, and all mutable catalog/Operations state. The public grid is not a database retirement mechanism.

## Local acceptance gates

1. `git diff --check` clean, source based on the approved exact revision, no unexpected files.
2. Backend full `pytest` passes (539 tests were reported before this documentation pass; verify again at release), frontend `npm run build` passes.
3. Exactly one Origin card appears in public catalog, with the configured family display order unaffected.
4. Standard `DD5RO` defaults; both selector options load their own images/specifications; switch back works without scrolling to the top; refresh, direct URLs and browser Back/Forward work.
5. Both availability inquiry and product-linked support headings display **Origin — Standard** and **Origin — Remineralization**; selected product ID remains correct on submission/Operations records.
6. No legacy Alkaline Plus recommendation appears in DD5RO overview; other product families/forms remain accurate; mobile headings/button/callout render at narrow widths.
7. Inquiry Turnstile/CSRF/backend validation remains in place; do not claim new protections were introduced by this release.

## Exact-revision production workflow and rollback boundary

Follow `DEPLOYMENT_AND_ROLLBACK.md` and `REBUILD_RUNBOOK.md` without substituting ad-hoc copy commands:

1. Validate/commit the reviewed source+documentation; confirm the exact 40-character Git SHA, clean tree, and authorized push.
2. Stage precisely that SHA using `scripts/production/stage_release_rsync.sh`; verify staged source integrity.
3. Capture the active release and confirm healthy baseline; run the guarded deployment helper, which creates a pre-deployment PostgreSQL backup, applies pending migrations if any, reconciles canonical catalog metadata, creates/activates an immutable release and runs readiness/HTTPS/security tests.
4. **No new Alembic revision is included in this Origin milestone.** The known current schema head is `c1e4f9b73a62`. Expect the catalog reconciliation to report the DD5RO description update, while inspecting any unexpected additional change before release acceptance. Do not hardcode a total change count: actual production data determines it.
5. Browser-check both Origin direct links, single catalog card, SKU-specific content, inquiry/support labels, refreshed copy, Back/Forward and mobile view. Verify the configured merchandising order remains intact.
6. If necessary, application rollback returns to the previous immutable application release, but **does not restore seed-owned catalog descriptions** or undo database changes. For rollback of the canonical description, use a separately reviewed source/catalog reconciliation or authorized database recovery plan; never assume application rollback reverses catalog writes. PostgreSQL backup creation is not proof of successful restore.
7. Reconcile this page and relevant runbooks after verified deployment. Keep future installation services, pricing and add-on commerce commissioning as separate business decisions.

## Deferred work

- Product-family/order-related unified toast visual uniformity across theme/font variants is explicitly deferred.
- Product inquiry honeypot parity and cross-worker/distributed rate limiting are separate hardening work; do not mislabel them as delivered.
- Formal cartridge add-on commerce, verified compatibility/pricing, and any promised installation services await separate product/client authorization.
