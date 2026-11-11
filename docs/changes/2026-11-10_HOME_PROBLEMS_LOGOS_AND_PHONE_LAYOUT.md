# 2026-11-10 — Problem-first home page, transparent logos, and phone layout

## Scope

- **Transparent logos.** Customer header and footer use the owner-supplied transparent artwork; the white plate behind the logo is removed and the header logo is larger (up to 252px wide on desktop, 164px on phones). Provenance and preparation are recorded in `frontend/public/brand/logos/README.md`. The black-line logo is inverted with CSS in dark appearance. Operations keeps its white logo plate.
- **Home page rhythm.** Section padding is reduced and the hero is sized by its content instead of filling the window.
- **Problem-first section.** New "What would you like to fix about your water?" section directly under the hero: five problems, each naming the kind of system that addresses it and linking to that family, plus a sixth card that opens the expert inquiry. Component: `frontend/src/components/home/WaterProblemsSection.tsx`.
- **Headline wording.** Hero label is "Premium Water Systems"; the hero action is "Help Me Choose a System".
- **Let us help you choose a system.** Replaces "Recommend a System". Starting points are framed as problems, and "power" and "backwash" are replaced by "an electrical outlet and a drain near where the system goes" and "systems that rinse themselves". Guided-question labels use the same plain language.
- **Customer wording for recommendation results.** The public page maps each result code to customer wording. The API titles and descriptions, the stored decision record, and Operations are unchanged; recommendation policy version stays `3`.
- **Phone layout.** Up to 720px wide, the primary navigation collapses behind a Menu button. On landscape handsets (up to 500px tall) the hero and catalog photographs fit the screen, and the product page keeps the photograph and thumbnails in view beside the details.
- **Footer.** The "Local API" status line is shown only in developer mode.

## Wording that needs supporting documentation

- The laundry-odor card states that Essence carbon filtration "is intended to capture the chemicals and sulfides that can leave an odor in your water and your wash". This follows owner direction of 2026-11-10 and is more specific than the Essence catalog description. `docs/PT14_CLIENT_PRODUCT_DIRECTION.md` asks for manufacturer documentation behind named substances.
- The hard-water card describes scale building up inside pipes and water heaters. It does not claim that any system extends plumbing life.

## Deployment

No schema migration, no backend change, and no catalog change: catalog reconciliation is expected to report `total_changes 0`.

Stage the exact commit from the development Mac:

    scripts/production/stage_release_rsync.sh <commit> dacqua-prod

Activate it on the production host:

    sudo /home/n8/dacqua-dolce-deploy-source/scripts/production/deploy_release.sh /home/n8/dacqua-dolce-deploy-source

## Rollback

The release active before this deployment was `20261110T220239Z` (revision `621eaba708bc373fd7e0178fe39d3c24446d64f7`). To return to it, on the production host:

    sudo /srv/dacqua-dolce/current/scripts/production/rollback_release.sh 20261110T220239Z

This release changes no database state, so the rollback is complete on its own.

## Validation before deployment

- `npm --prefix frontend run typecheck`
- `node --test frontend/tests/*.test.mjs` — 25 passing
- Production-mode frontend build
- Browser checks at 1440x900, 393x852, 852x393, and 932x430

Not checked in a browser: dark appearance, the other themes, and a full pass through the guided questions.
