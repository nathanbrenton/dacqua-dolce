# 2026-11-14 — "$" price inputs, folded request configuration, smoother request scrolling

## Scope

- **Price inputs.** Operations price fields (formal quote "Quoted unit price" and commercial adjustment amounts; Catalog price and promotional price) show a fixed "$" prefix (`frontend/src/components/operations/MoneyInput.tsx`). A typed or pasted "$" is dropped as it is entered. When saving, a leading "$", thousands commas and spaces are accepted, so "$2,500.00", "2,500" and "2500.00" all parse as $2,500.00 (`operationsMoney.ts`, tested by `frontend/tests/operations-money.test.mjs`).
- **Folded configuration.** A product inquiry's server-written configuration summary ("Customer-requested configuration …") is folded under a "Requested configuration" disclosure showing the SKU and family; the customer's own message is shown below it. The stored message is unchanged.
- **Scrolling.** A request's Conversation no longer scrolls inside its own box, which captured the mouse wheel (`overscroll-behavior: contain`). It shows the latest three emails with a "Show N earlier emails" button, and the page scrolls normally over it.
- **Deploy output.** `scripts/production/deploy_release.sh` ends by printing the rollback command for the release that was active before. This first appears when activating this release.

## Deployment

No schema migration, no backend change, and no catalog change: catalog reconciliation is expected to report `total_changes 0`.

Stage the exact commit from the development Mac:

    scripts/production/stage_release_rsync.sh <commit> dacqua-prod

Activate it on the production host:

    sudo /home/n8/dacqua-dolce-deploy-source/scripts/production/deploy_release.sh /home/n8/dacqua-dolce-deploy-source

## Rollback

The release active before this deployment was `20261114T232900Z` (revision `baa20dfc1fea5c67374c7440a99857f756639049`). To return to it, on the production host:

    sudo /srv/dacqua-dolce/current/scripts/production/rollback_release.sh 20261114T232900Z

This release changes no database state, so the rollback is complete on its own.

## Validation before deployment

- `npx tsc -p tsconfig.app.json --noEmit` (frontend)
- `node --test frontend/tests/*.test.mjs` — 27 passing
- Production-mode frontend build; `bash -n` on the deploy script
- Browser checks at 1440x900 (local, light and dark): typing "$2,500.00" into the quoted unit price leaves "2,500.00"; the configuration folds and unfolds; wheel scrolling over the Conversation moves the page; "Show 1 earlier email" reveals the fourth email

Not checked: saving a formal quote with a "$"-prefixed amount end to end (covered by the unit test), and the Catalog price inputs in a browser (the test account cannot edit pricing).
