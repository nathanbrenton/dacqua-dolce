# 2026-11-15 — Header and footer show the same logo

## Scope

- **One logo everywhere.** The header, footer and Operations show the same artwork: whichever "Logo artwork" option is picked in the pop-up behind the footer logo. Before, the footer always swapped in the "Filtration Systems" version on its own.
- **Default: Metallic / Aqua without the subtitle** (`/brand/logos/dacqua-dolce-logo-metallic-aqua-transparent.webp`, already on the site). The saved choice moved to the `dacqua-dolce-logo-v3` browser storage key, so each visitor's earlier pick resets to this default once. Picking another option still works and is remembered.
- No new image files. Code: `theme/branding.ts` (the unused per-variant `filtrationPath` is gone), `BrandLogo.tsx`, `DeveloperFooterLogo.tsx`, `App.tsx` (storage key).

## Deployment

No schema migration and no catalog change: catalog reconciliation is expected to report `total_changes 0`.

Stage the exact commit from the development Mac:

    scripts/production/stage_release_rsync.sh <commit> dacqua-prod

Activate it on the production host:

    sudo /home/n8/dacqua-dolce-deploy-source/scripts/production/deploy_release.sh /home/n8/dacqua-dolce-deploy-source

## Rollback

The release active before this deployment was `20261115T010837Z` (revision `e5a7ee212123f26e6f9d7b3fcd5cbd2abd8022f8`). To return to it, on the production host:

    sudo /srv/dacqua-dolce/current/scripts/production/rollback_release.sh 20261115T010837Z

After a rollback the footer shows the Filtration Systems version again, and visitors' earlier saved picks (under the old `v2` key) apply again.

## Validation before deployment

- `npx tsc -p tsconfig.app.json --noEmit` (frontend)
- `node --test frontend/tests/*.test.mjs` — 29 passing
- Production-mode frontend build
- Browser check (local): by default header and footer both load the plain metallic file; switching to "Monochrome + Filtration Systems" changes both, and switching back restores both.

No backend change, so the backend suite was not rerun.
