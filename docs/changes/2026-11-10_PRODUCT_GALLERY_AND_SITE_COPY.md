# 2026-11-10 — Product gallery, image viewer, and public copy rewrite

## Scope

- **Pinned product gallery (desktop).** On windows wider than 900px and taller than 600px the gallery stays in view while product details scroll. The main photograph is scaled to fit, never cropped, so the photograph, its thumbnails, and the image notice are all visible without scrolling. Narrower or shorter windows, including phones in either orientation, keep the scrolling layout.
- **Enlarged image viewer.** Clicking the main photograph opens it as large as the window allows. Escape, the close button, or the area around the photograph closes it. With a mouse, hovering the enlarged photograph magnifies the area under the cursor (2x–3x); clicking the photograph does not close the viewer. Touch screens have no hover zoom; a tap closes the viewer.
- **Product page order.** Identity, promise and at-a-glance points, overview, configuration, price/quote action, CLEAR Technology, care and maintenance, specifications, warranty and support. The quote action now follows configuration directly. The CLEAR section still sits between configuration and the care section, and the PureLine maintenance notice still closes the Harmony configuration block, as accepted in PT54-G2.
- **Public copy.** Home, catalog cards, Recommend a System, product pages, quote dialog, Support page, and the Terms/Privacy status pages are rewritten in plain customer language. Internal and compliance phrasing is removed; each caveat is stated once.
- **Catalog descriptions.** Nine product descriptions in `backend/catalog/production_catalog.json` are rewritten. `Big Blue` is removed from the DD15CLEARPTV description because PT14 reserves it as a non-public term.

## Deliberately unchanged

- The product image disclaimer and the PureLine maintenance notice (`productNotices.json`) are verbatim.
- No new facts: no response times, sizing guidance, or prices were added.
- Sign-in, account, password, and verification screens; system email; published policy text.
- No schema migration. No backend code change.

## Wording that needs client confirmation

- The CLEAR explanation now uses the "preferred customer-facing explanation" from `docs/PT14_CLIENT_PRODUCT_DIRECTION.md`. That document also records the mechanism as subject to technical verification.
- "A quote request is not an order" (product page) and "Our team will review it and reply by email" (quote confirmation) describe the current workflow rather than a written policy.

## Deployment

From the repository on the development Mac, stage the exact commit:

    scripts/production/stage_release_rsync.sh <commit> dacqua-prod

Then, on the production host, activate it:

    sudo ~/dacqua-dolce-deploy-source/scripts/production/deploy_release.sh ~/dacqua-dolce-deploy-source

Catalog reconciliation is expected to report `products_updated 9` and `total_changes 9` on the first deployment of this change, and `0` afterwards.

## Rollback

The release active before this deployment was `20261104T001004Z` (revision `e66f22470dcd861ce48cc849251eed3927c403b4`). To return to it, on the production host:

    sudo /srv/dacqua-dolce/current/scripts/production/rollback_release.sh 20261104T001004Z

To list the releases available for rollback, run the same helper with no argument:

    sudo /srv/dacqua-dolce/current/scripts/production/rollback_release.sh

Rollback switches the application release and restarts the API. It does not touch PostgreSQL, so the nine rewritten catalog descriptions remain in the production database after a rollback. The previous release displays them without error. To restore the earlier descriptions as well, stage and deploy revision `e66f22470dcd861ce48cc849251eed3927c403b4` with the deployment commands above, which re-runs catalog reconciliation from that revision's manifest.

Release retention defaults to five, so `20261104T001004Z` stays available until four further releases have been deployed.

## Validation before deployment

- `npm --prefix frontend run typecheck`
- `node --test frontend/tests/*.test.mjs` — 25 passing
- Production-mode frontend build
- `backend/.venv/bin/python -m ruff check backend`
- `backend/tests/test_seed_catalog.py` — 6 passing
- `python -m app.cli.seed_catalog plan` against the local development database — 9 product updates, no other changes
- Browser checks at 1024x620, 1280x720, 1440x900, 1920x1080, 2560x1440, and 393x852

The full backend test suite was not run for this change: it needs the isolated PostgreSQL test cluster, and the only backend file changed is the catalog manifest.
