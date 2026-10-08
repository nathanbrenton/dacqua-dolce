# PT33-B v0.4 — Sanitized production evidence (offline)

**Status:** Local planning only; `ready_to_apply=false` for all assessments.

## What was observed

The resource snapshot `production-evidence.2026-10-08.json` was transcribed from user-provided read-only terminal output from D’Acqua's Debian 13 host, on October 8, 2026. It lists observed TCP listeners, selected loaded service names, three D’Acqua paths, PostgreSQL database names, and PostgreSQL login roles. The original inspection did **not** record a UTC timestamp, so `collected_at_utc` is null, and the checker reports calendar-day precision. Do not pretend this is a timestamped automated probe.

**Limits:** The service-unit list does not enumerate all installed unit files; service-user inspection was not exhaustive; listening TCP sockets do not prove port availability; PostgreSQL query listed login roles, not every role; NGINX sites-enabled filenames are not effective vhost names. All relevant coverage is marked partial unless the corresponding SQL query was comprehensive within its stated scope. A positive collision blocks a plan; lack of a collision never approves a plan. The inventory must be refreshed and reconciled with the actual target host and independent third-party provider accounts before provisioning. The source snapshot is a dated historical artifact, not an automatically refreshed truth source.

Do not place provider IDs, tokens, API keys, environment values, customer data, or secrets in inventory. The file includes an infrastructure hostname and service identifiers, so review before sharing. If reviewing the effective NGINX configuration later, **do not** upload `nginx -T` output verbatim; it may include sensitive values.

## LOCAL macOS — Offline assessment

```bash
cd "$HOME/Desktop/dacqua-dolce"
python3 scripts/pt33/evaluate_production_evidence.py \
  --manifest docs/production/pt33/business-manifest.example.json \
  --evidence docs/production/pt33/production-evidence.2026-10-08.json
```

The checker validates provenance fields and rejects missing coverage, unrecognized scope, future or stale inspection dates (default maximum one calendar day), and conflicts. It always refuses to claim apply readiness. The inspection target is **the existing D’Acqua host**, not a different business's independent hosting account.

## Next gates

1. Inventory authorized target hosting account separately, using read-only commands with exact clock time and permissions scope.
2. Obtain complete systemd installed-unit, Unix account, effective vhost name, firewall, backup, database-role, and IPv4/IPv6 port evidence without disclosing secrets.
3. Validate provider ownership via each business's own account/login; record status without credentials.
4. Add an explicit evidence bundle linking manifest instance ID to host identity and provider account attestations. Never promote an offline absence check into authorization.
