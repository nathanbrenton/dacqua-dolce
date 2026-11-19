# 2026-11-18 — Operations and account pages split into smaller files; saves show immediately

## Scope

- **Saved changes show straight away (behaviour change).**
  - Staff: saving an account's role replied with the roles it had before the change, so the Access badge only updated after a second save. `load_user_with_roles` in `backend/app/services/account_administration.py` now reloads with `populate_existing=True`, so the reply carries the new roles (this also covers the status save). New test in `backend/tests/test_account_administration.py`.
  - Overview: the summary counts and readiness snapshot are refetched after any Catalog save and after a policy approval or import, instead of only on page load.
  - Inbox: a reply sent from inside a request goes straight into the Inbox list, the open conversation and "Needs you", instead of waiting for the next refresh.
- **Code reorganisation, no intended behaviour change.**
  - `OperationsPage.tsx` (6,242 lines) is now about 800 lines. Each tab has its own file in `frontend/src/components/operations/workspaces/`. Catalog's product card and its editors are in `operations/catalog/`, and a request's detail pane is in `operations/requests/`.
  - `AccountPage.tsx` (2,337 lines) is now 435 lines. The security and appearance panels have their own files, and each customer panel is in `components/account/sections/`.
  - Two small differences in how state is held:
    - Each Catalog editor now keeps its own product's draft.
    - Notify When in Stock requests load inside the Catalog tab rather than at page start.
- **Docs only.**
  - CLAUDE.md has the new file map and updated local-agent notes.
  - An OpenCode `/catchup` command was added (`.opencode/commands/catchup.md`, from 205bb84).

Commits since the active release: 205bb84, f6f1f57, 3265c8d, cb05526, 3106217, bbddd6a, 3d5d1be, plus this note.

## Deployment

No schema migration and no catalog change: catalog reconciliation is expected to report `total_changes 0`.

Stage the exact commit from the development Mac:

    scripts/production/stage_release_rsync.sh <commit> dacqua-prod

Activate it on the production host:

    sudo /home/n8/dacqua-dolce-deploy-source/scripts/production/deploy_release.sh /home/n8/dacqua-dolce-deploy-source

## Rollback

The release active before this deployment was `20261115T183311Z` (revision `e3cda6c4d4cc743c0ab4322f79b6173ce7b398d5`). To return to it, on the production host:

    sudo /srv/dacqua-dolce/current/scripts/production/rollback_release.sh 20261115T183311Z

After a rollback, the Staff Access badge again needs a second save to show a role change, and Overview counts and the Inbox again catch up only on reload or refresh.

## Validation before deployment

- `npx tsc -p tsconfig.app.json --noEmit` (frontend), after each stage
- `node --test frontend/tests/*.test.mjs`: 29 passing
- Production-mode frontend build
- `ruff check backend`; full backend regression: 737 passing, including the new role-reload test
- Role reload checked against the local database inside a rolled-back transaction: the old reload replied `['employee']` after the role was removed, the fixed one `[]`.
- Browser checks (local, 1440×900):
  - **Employee account:** all seven Operations tabs it can open render.
    - Requests filters, selection and notes drafts behave as before.
    - "Open in Inbox" and "Open request" link the two tabs both ways.
    - Overview tiles open the right requests.
    - The Catalog editors start from each product's data.
    - Customer search works.
  - **Customer account:** all 11 panels show in the original order.
    - The profile saves and shows the "Profile updated." toast.
    - The add-address form opens and closes.

**Not yet checked:** Staff and Audit, and any administrator save (roles, catalog, equipment). These need an administrator or developer account with MFA. Check them after activating.
