# PT33-B v0.3 — Read-only scoped host evidence (initial iteration)

**Status:** Development-only host observations; never an apply authorization.

`python3 scripts/pt33/collect_host_inventory.py --manifest docs/production/pt33/business-manifest.example.json --schema docs/production/pt33/business-manifest.schema.json --output "$HOME/Desktop/pt33b-host-inventory.json"`

The output JSON is created exclusively (`0600`) and never overwritten. It contains proposed identifiers, observation results, inspection timestamp and host name; review the report before sharing, especially when a hostname is sensitive. No environment variables, private keys, database records, service command lines, or provider credentials are read. The script never SSHes into production. To inspect another host, copy/review the source and manifest on that host and invoke locally with explicit authorization; do not automatically run it on production.

Checks: named OS user (`pwd`), expected systemd file locations (Linux only; partial coverage), existence of three proposed paths, visible listening TCP port via `lsof` (partial coverage). **Absence observed does not mean available.** Running processes, permissions, other unit paths, UDP, effective NGINX, PostgreSQL, DNS, backups, remote hosts, and provider ownership remain unverified. The report always sets `ready_to_apply=false`.

This is intentionally **not yet compatible with PT33-B v0.2's manually supplied `offline-inventory.example.json` contract**. It is evidence to review, not an automatically trusted collision inventory. The next step is an explicit evidence-to-inventory adapter with provenance/freshness and refusal for missing categories. Never treat an observation from a different host as authoritative for the target.
