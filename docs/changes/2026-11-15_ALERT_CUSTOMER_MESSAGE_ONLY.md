# 2026-11-15 — New-request alert shows only the customer's message

## Scope

- **Shorter alert body.** The email sent to `DACQUA_EMAIL_OPERATOR_TO` keeps the contact details (name, email, phone, preferred contact method, product family) and the "Message:" heading, then shows only the customer's own words. For configured product requests, the "Customer-requested configuration (NOT a priced or approved order)" summary is left out; it stays on the request in Operations. A configured request with no customer text shows "(No message)". The closing line "Full details are in Operations > Requests." is removed.
- Code: `customer_message_text` in `backend/app/services/product_configuration.py` (mirrors the Operations frontend's `splitRequestMessage`), used by `send_quote_emails` in `backend/app/api/quotes.py`. The stored request message is unchanged.
- **Docs only:** certificate renewal on the host. `docs/production/OPERATIONS_REFERENCE.md` and `REBUILD_RUNBOOK.md` (section 15) record the certbot deploy hook `/etc/letsencrypt/renewal-hooks/deploy/50-reload-nginx`, installed and dry-run tested on 2026-11-15, which reloads nginx after each renewal.

## Deployment

No schema migration and no catalog change: catalog reconciliation is expected to report `total_changes 0`.

Stage the exact commit from the development Mac:

    scripts/production/stage_release_rsync.sh <commit> dacqua-prod

Activate it on the production host:

    sudo /home/n8/dacqua-dolce-deploy-source/scripts/production/deploy_release.sh /home/n8/dacqua-dolce-deploy-source

## Rollback

The release active before this deployment was `20261115T012348Z` (revision `81b05de5ed950555ff9ba9e25816204514a0f2b0`). To return to it, on the production host:

    sudo /srv/dacqua-dolce/current/scripts/production/rollback_release.sh 20261115T012348Z

After a rollback, alerts include the configuration summary and the closing line again.

## Validation before deployment

- `ruff check backend`; full backend regression — 736 passing, including two new alert tests (configuration summary left out; configuration with no customer text)

No frontend change.
