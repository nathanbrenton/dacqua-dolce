# 2026-11-15 — Customer name in new-request alert subjects

## Scope

- **Alert subject.** New-request alerts sent to `DACQUA_EMAIL_OPERATOR_TO` now carry the customer's name: "New expert inquiry — Jamie Smith", "New product inquiry — …", "New recommendation inquiry — …" or "New quote request — …". Whitespace and line breaks in the name are collapsed and the name is cut at 120 characters; with no name the subject is the plain label. The body is unchanged.
- **Why.** Identical subjects made mail apps stack every alert into one thread and read them as bulk mail. Apple Mail on iPhone filed them under Promotions; that is decided on each phone, and is fixed once per phone with ⋯ → Categorize Sender → Primary. The subject change makes each alert distinct but cannot force a category.

## Deployment

No schema migration, no frontend change, and no catalog change: catalog reconciliation is expected to report `total_changes 0`.

Stage the exact commit from the development Mac:

    scripts/production/stage_release_rsync.sh <commit> dacqua-prod

Activate it on the production host:

    sudo /home/n8/dacqua-dolce-deploy-source/scripts/production/deploy_release.sh /home/n8/dacqua-dolce-deploy-source

## Rollback

The release active before this deployment was `20261115T001255Z` (revision `bdf986420b79afd0ab1de9a51bd7a93da28de1f0`). To return to it, on the production host:

    sudo /srv/dacqua-dolce/current/scripts/production/rollback_release.sh 20261115T001255Z

This release changes no database state, so the rollback is complete on its own.

## Validation before deployment

- `ruff check backend`
- Full backend regression — 721 passing (alert tests cover the subject with a name and with a name containing extra whitespace)

Not checked: a real alert arriving with the new subject (local email is suppressed).
