# Documentation Audit — 2026-10-06

Reviewed **62** documentation/reference files from the tracked `dacqua-dolce` documentation export.

## Current production reference

- Active deployed revision: `0dfc6329a4a8e9584fba4b00cba66512438fd21b`.
- Active release: `/srv/dacqua-dolce/releases/20261006T175805Z`.
- Alembic head: `f1c4a5b76e80`.
- PT47-PT51 production browser acceptance: complete.
- PT52/PT53 deployment smoke validation: complete; final production browser acceptance not yet recorded at audit time.
- Commerce Launch Gate: intentionally closed.

## Corrections made

- Replaced PT18/PT24-era current-state claims in living production-facing docs.
- Reconciled observability mail as commissioned; only Better Stack delivery-heartbeat integration remains pending.
- Reconciled weekly observability recipients to include `nathan@nathanbrenton.com`, `jamie.dacqua.dolce@gmail.com`, and `dacquadolce@proton.me`.
- Added PT47-PT53 operations/application state to living documentation.
- Documented Git vs Production PostgreSQL authority and PT53 manual policy portability.
- Documented that Restic/S3 is backup/DR, not environment synchronization.
- Kept live tax, Affinity24 gateway, legal review, shipping-insurance, public support phone, and public installer-program dependencies explicit rather than inventing completion.

## Files updated

- `README.md`
- `docs/CLIENT_NOTES_IMPLEMENTATION_MATRIX.md`
- `docs/LOCAL_DEVELOPMENT.md`
- `docs/OPERATIONS_AND_PRICING_GOVERNANCE.md`
- `docs/PRODUCTION_DEPLOYMENT_FOUNDATION.md`
- `docs/PRODUCTION_HOST_BOOTSTRAP.md`
- `docs/PRODUCTION_HOST_RUNBOOK.md`
- `docs/PRODUCTION_SECRET_BOUNDARY.md`
- `docs/production/ARCHITECTURE_OVERVIEW.md`
- `docs/production/COMMUNICATIONS_AND_POSTMARK.md`
- `docs/production/DEPLOYMENT_AND_ROLLBACK.md`
- `docs/production/OPERATIONS_REFERENCE.md`
- `docs/production/PENDING_INTEGRATIONS.md`
- `docs/production/README.md`
- `docs/production/REBUILD_RUNBOOK.md`

## Historical milestone records preserved

Historical PT milestone documents (30 files) were reviewed as dated implementation records and were not rewritten merely to make their original prose read as current state. Living docs now provide the current reconciliation layer.

## Other files reviewed without change

- `backend/catalog/README.md`
- `backend/constraints-known-good.txt`
- `docs/DACQUA_DOLCE_AUDIENCE_LEXICON.md`
- `docs/EMAIL_AND_PASSWORD_RECOVERY.md`
- `docs/ENVIRONMENT_IDENTITY.md`
- `docs/LOCAL_ROLE_BOOTSTRAP.md`
- `docs/OPERATIONS_UI_CONSISTENCY.md`
- `docs/PAYMENT_DATA_BOUNDARY.md`
- `docs/PAYMENT_PROVIDER_COMMISSIONING.md`
- `docs/PHONE_DATA_HANDLING.md`
- `docs/POST_PURCHASE_REMINDER_RUNBOOK.md`
- `docs/PRODUCT_IMAGE_ASSETS.md`
- `docs/PYTHON_DEPENDENCY_POLICY.md`
- `docs/RECOMMENDATION_ARCHITECTURE.md`
- `docs/THIRD_PARTY_FONTS.md`
- `docs/production/GRAFANA_DASHBOARDS.md`
- `frontend/public/brand/logos/README.md`

## Authority rule

Use `docs/production/` for current production operations/rebuild truth. Use dated PT documents for milestone history. Do not infer current production state from old milestone, planning, or bootstrap prose when the living production docs supersede it.
