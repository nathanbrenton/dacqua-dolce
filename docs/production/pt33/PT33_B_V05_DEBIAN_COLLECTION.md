# PT33-B v0.5 — Debian Collector, Increment 2

This increment is a **bounded observation layer**, not comprehensive verification or provisioning approval. It extends the existing v0.5 contract and does not replace the v0.3 macOS collector. The evidence evaluator remains offline. `ready_to_apply=false` is mandatory.

## Concepts and limits

- `getent passwd` enumerates visible Name Service Switch identities; directory users may not appear. Status stays **partial** even after command success. No password hashes or shadow files are read.
- `systemctl list-unit-files --all --no-pager --no-legend --plain` lists systemd unit-file identifiers, including many timers, but not necessarily transient units, all aliases, or effective overrides. Status stays **partial**.
- `ss -H -ltn` lists visible listening TCP sockets; the evidence retains only numeric ports, **not addresses, UDP sockets, or network namespaces**. Status stays **partial**. A port observed on one address can be a collision candidate, but absence does not prove availability.
- Filesystem paths, NGINX configuration, PostgreSQL catalogs, group identifiers and provider accounts are **not collected** by this increment. Database/role/path sections explicitly remain unsupported, and independent provider ownership always remains unverified. Their verification is deferred to additional carefully reviewed read-only collection methods.
- The SHA-256 list digests detect accidental edits but do not authenticate the collector or host. `host_id` is a self-reported sanitized hostname label, not proof of host identity.
- Command failures, output truncation, inaccessible tools and malformed rows never become complete evidence. Command timeout is eight seconds and output cap is two megabytes. The collector never invokes a shell or `sudo`.

## Dependency-ordered workflow

1. **LOCAL macOS:** inspect the manifest and the already committed canonical schema. Run existing PT33 tests. Do not run the new Linux collector locally; it explicitly rejects macOS.
2. **PRODUCTION Debian (only after separate approval):** transfer reviewed source, canonical manifest/schema and dependencies using the approved safe release process; do not place anything in application service paths merely for evidence collection. Verify collector source hash and runtime prerequisites (`python3`, `getent`, `systemctl`, `ss`). Do not run the collection as root by default. Review filesystem permissions and approved output destination.
3. **PRODUCTION Debian:** `python3 scripts/pt33/collect_debian_evidence.py --manifest docs/production/pt33/business-manifest.example.json --output "$HOME/pt33-observation.json"` is an **illustrative invocation only**, not a live production instruction. `--manifest` selects a separately validated proposed business manifest; `--output` exclusively creates a private mode-0600 JSON file and refuses overwrite. Use an explicit approved transfer/export path for evidence; review and sanitize the file before sharing.
4. **LOCAL macOS:** inspect the sanitized v0.5 evidence and run `python3 scripts/pt33/evaluate_production_evidence.py --manifest <approved-manifest> --evidence <sanitized-evidence> --max-age-hours 24`. The age policy is explicitly selected; 24 hours is a conservative review default, not proof of availability. Do not treat any observed absence as clearance unless the section is independently verified complete (this collector does not emit complete sections).
5. Verify provider ownership separately in each new business's registrar, Cloudflare, hosting/Vultr, Proton, Postmark, Better Stack and AWS dashboards. Do not place authentication credentials or account recovery data into observation JSON. Production launch remains blocked pending independent approvals.

## Recovery

If a command is missing or permission-limited, the section is reported `failed` rather than empty-and-complete. Re-run only after documenting and approving an appropriate safe inspection method. Refuse overwrite, delete only your own unused temporary evidence outputs after records are safely transferred, and never solve a permission failure by silently escalating to root. Future increments must add source-aware, address-aware and namespace-aware collectors before asserting comprehensive collision coverage.
