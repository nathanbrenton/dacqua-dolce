# 2026-11-15 — Origin product pages no longer offer the neoprene jacket

## Scope

- **Product page.** The "Black Neoprene Jacket (+$100)" checkbox is no longer shown on Origin pages (DD5RO Five Stage, DD6ROAE Six Stage). Origin is an under-sink reverse-osmosis system; the jacket fits the whole-house tanks only. Refine, Essence and Harmony are unchanged.
- **No carry-over.** A jacket chosen on another family's page is ignored on Origin pages: Origin photography, the "price does not include the jacket" note and the quote request text always treat Origin as having no jacket (`jacketOffered` / `effectiveTankFinish` in `ProductDetailPage.tsx`).
- **Already excluded, unchanged:** the server's jacket-eligible SKUs never included Origin, product-configuration requests reject a finish for Origin (now covered by a backend test), and the Operations formal-quote jacket checkbox only appears for eligible SKUs.

## Deployment

No schema migration, no backend change, and no catalog change: catalog reconciliation is expected to report `total_changes 0`.

Stage the exact commit from the development Mac:

    scripts/production/stage_release_rsync.sh <commit> dacqua-prod

Activate it on the production host:

    sudo /home/n8/dacqua-dolce-deploy-source/scripts/production/deploy_release.sh /home/n8/dacqua-dolce-deploy-source

## Rollback

The release active before this deployment was `20261115T000018Z` (revision `f8aa2560f309fb73187da73040092f446ca3576d`). To return to it, on the production host:

    sudo /srv/dacqua-dolce/current/scripts/production/rollback_release.sh 20261115T000018Z

This release changes no database state, so the rollback is complete on its own.

## Validation before deployment

- `npx tsc -p tsconfig.app.json --noEmit` (frontend)
- `node --test frontend/tests/*.test.mjs` — 28 passing (three source-pinning tests updated to the new condition names; one new Origin test)
- Backend product-configuration and neoprene pricing tests — 27 passing
- Production-mode frontend build
- Browser check (local): both Origin pages show no jacket text or checkbox; the Refine DD15SOFT page still shows it
