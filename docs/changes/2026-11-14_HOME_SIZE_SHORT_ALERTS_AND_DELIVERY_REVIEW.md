# 2026-11-14 — Home size on the quote form, short new-request alerts, and clearing failed emails

## Scope

- **Approximate household size.** The quote form's "Household size" number box is now a dropdown, "Approximate household size", in square-foot ranges: Not sure, under 1,000, 1,000–1,500, 1,500–2,000, 2,000–2,500, 2,500–3,000, 3,000–4,000, 4,000–5,000, over 5,000. It is stored as `home_size` in the request's recommendation context (optional; older requests are unaffected). Operations shows the range as written. A head count carried over from the recommendation tool is still sent. For sizing readiness, either a head count or a home size satisfies "household size". The recommendation tool's "Number of occupants" field is unchanged, and the recommendation policy version stays `3`.
- **Shorter new-request alert.** The email sent to `DACQUA_EMAIL_OPERATOR_TO` now holds only the customer's name, email, phone, product family and message, plus a pointer to Operations > Requests. Subjects drop the brand name, which the sender already shows: "New product inquiry", "New expert inquiry", "New recommendation inquiry", or "New quote request".
- **Mark failed emails reviewed.** Inbox > Delivery issues has "Mark reviewed" on each failed email and "Mark all N reviewed". Reviewed failures leave Delivery issues, the "Email failures" count and the Overview "Needs you" list. New endpoint `POST /api/operations/communications/review` (operations roles), with a `communications.delivery_reviewed` audit event per delivery.

## Deployment

**Schema migration:** `e4b7c2d91f05` adds two nullable columns to `email_deliveries` (`reviewed_at`, `reviewed_by_user_id` → `users.id`, `ON DELETE SET NULL`). The deploy script runs it. No catalog change: catalog reconciliation is expected to report `total_changes 0`.

Stage the exact commit from the development Mac:

    scripts/production/stage_release_rsync.sh <commit> dacqua-prod

Activate it on the production host:

    sudo /home/n8/dacqua-dolce-deploy-source/scripts/production/deploy_release.sh /home/n8/dacqua-dolce-deploy-source

After activation, the 4 failed new-request alerts from October can be cleared with Inbox > Delivery issues > "Mark all 4 reviewed".

## Rollback

The release active before this deployment was `20261114T070100Z` (revision `2416b6ae953d29d0c557522bf560a875bf6a3ef1`). To return to it, on the production host:

    sudo /srv/dacqua-dolce/current/scripts/production/rollback_release.sh 20261114T070100Z

The rollback leaves the two new columns in place. The previous release does not read them, so it runs normally, but failures marked reviewed would show again until this release is restored.

## Validation before deployment

- `npx tsc -p tsconfig.app.json --noEmit` (frontend)
- `node --test frontend/tests/*.test.mjs` — 26 passing
- Production-mode frontend build
- `ruff check backend`; full backend regression — 718 passing, including the migration on a fresh database
- Browser checks at 1440x900 (local): the quote form dropdown, and marking failed emails reviewed one by one through to an empty Delivery issues and "Email failures 0"

Not checked: a real alert email in the new format (local email is suppressed, so this is covered by unit tests only), and dark appearance for the Delivery issues buttons.
