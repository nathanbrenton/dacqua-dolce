# PT33-B v0.5 — Integrated offline resource assessment (Increment 7)

## Purpose and boundaries

This is a **planning/evidence workflow**, not an infrastructure installer, account creator, or authorization system. It is designed for a new **independently deployed** business instance, not a multi-tenant account. It never provisions resources and always outputs `ready_to_apply=false`. Preserve D'Acqua Dolce production unchanged. Do not copy customer databases, live credentials, mailboxes, backup encryption keys or secret-bearing NGINX configuration into a new business.

The workflow validates a business manifest, consumes one sanitized v2 host snapshot, checks explicitly observed collisions, and writes a non-authorizing report. Missing identifiers in `partial`/`failed`/`unsupported` sections **remain unverified**. A `complete` claim is bounded by its declared scope, not proof that allocating a resource is safe. Snapshot SHA-256 digests detect changed lists, **not who collected them**; `host_id` is a label, not authenticated host identity.

## Key terminology

- **Manifest:** Proposed new-business identity and resource requests. `business-manifest.schema.json` constrains fields; `plan_business.py` adds semantic checks (including protected D'Acqua Dolce identifiers).
- **Evidence:** Version 2 JSON with UTC collection timestamp, declared single-host scope, source label, resource sections, digest per section, and explicitly unverified external providers.
- **Collision:** Positive observed identifier or path overlap. Always blocks allocation until independently investigated.
- **Not observed in declared scope:** A claim only about the inventoried source; NOT a promise of future availability.
- **Unverified:** Partial, failed, stale, inaccessible, contradictory, or out-of-scope evidence. Stale/invalid snapshots are refused entirely.

## Dependency-ordered procedure

### 1. LOCAL macOS — prepare and test (no host access)

Operate from the existing `~/Desktop/dacqua-dolce` repository. Keep the actual Git working tree and correct branch under review. Do not place production credentials in manifests; secret references are **logical names only**.

```bash
cd "$HOME/Desktop/dacqua-dolce"
python3 -m unittest discover -s scripts/pt33 -p 'test_*.py' -v
python3 scripts/pt33/plan_business.py --help
python3 scripts/pt33/verify_business_resources.py --help
```

Prepare a **new-business** manifest from `docs/production/pt33/business-manifest.example.json`, validating business names, instance ID, domains, database/role identifiers, desired service user/unit, paths, and port. The sample represents a schema example, not an authorization to use the sample domain or port in production. Do not repurpose an existing customer database or production credentials.

### 2. PRODUCTION Debian — approved read-only collection (NOT AUTHORIZED BY THIS INCREMENT)

Obtain separate explicit user approval before touching the host. Review the collector implementation, chosen Unix identity, target manifest, output location, and permission scope first. Collector `--help` is the entry point:

```bash
python3 scripts/pt33/collect_debian_evidence.py --help
```

When approved, the collector writes a new private-mode JSON file, refusing overwrite and restricted system paths. It queries `getent passwd`, `getent group`, `systemctl` unit identifiers, `ss` TCP listeners, and `lstat` for **only** candidate deployment paths. `--inspect-nginx` opts in to in-memory `nginx -T` parsing (the raw output may be sensitive; never paste it in chat). `--inspect-postgres` opts in to local noninteractive `psql` queries of `pg_catalog.pg_database.datname` and `pg_catalog.pg_roles.rolname` only. Those optional inspections are not authorized merely by this runbook. No `sudo`, privilege escalation, external networking or customer-table queries are needed for the collector.

On failures, retain the section as `failed` or `partial`; do not assume nonexistence. Verify collection provenance and inspect the sanitized JSON for private identifiers before exporting. Never share raw NGINX configuration, PostgreSQL authentication details, environment variables, session cookies, provider credentials or customer records.

### 3. LOCAL macOS — evaluate the sanitized evidence offline

Place **only reviewed, sanitized** v2 JSON outside public repositories. Use dedicated manifest/evidence/report paths. Example command, with placeholders replaced by actual safe files:

```bash
cd "$HOME/Desktop/dacqua-dolce"
python3 scripts/pt33/verify_business_resources.py --manifest /path/to/new-business-manifest.json --evidence /path/to/reviewed-v2-evidence.json --output /path/to/new-private-report.json --max-age-hours 24
```

`--max-age-hours` is an **explicit local review policy** in `(0, 720]` hours; 24 is the default, not a freshness guarantee. The evidence timestamp must be UTC and not future dated. Output refuses overwrite and is created with owner-only file permissions. Do not check reports containing business-specific inventories into a public Git repository. A rejected run exits nonzero and must not be interpreted as clearance.

Read `host_assessment.collisions`, `host_assessment.unverified`, and `host_assessment.not_observed` separately. The output includes manual provider gates and permanent `ready_to_apply=false`. Earlier v0.4 evaluation remains available through `evaluate_production_evidence.py`, but the integrated entry point **requires v2 evidence** rather than weakening v0.5 checks.

### 4. External provider gates — business administration, not host evidence

For each business, separately confirm **actual account ownership**, recovery access, billing, alert recipients and offboarding policy in the respective provider dashboard. The host collector cannot establish independent registrar/domain ownership, Cloudflare account and zone, Vultr server/billing, Proton identity and mailbox, Postmark server/sender credentials, Better Stack alerting, or AWS backup account/repositories. Separate tokens inside one shared third-party account are not proof of independence. Record approvals without exporting credentials.

### 5. Outstanding technical gates and next acceptance phase

- NGINX `server_name` extraction is partial; default-server/listen precedence, regex names, upstreams, duplicate blocks, includes and active-versus-on-disk state require careful review.
- PostgreSQL inspection sees **one accessible local cluster**; other clusters, ownership, privileges and role memberships remain unverified.
- Unix enumeration can omit directory/NSS identities; UID/GID requests are not yet part of the manifest contract.
- systemd inventory is not exhaustive for aliases, drop-ins, transient units or generator behavior.
- TCP listeners are point-in-time and may not cover all network namespaces, IPv6 binding interaction or future allocations.
- Filesystem path probes do not establish permission, ownership, mount/symlink topology exhaustively.
- TLS, DNS, firewalls, scheduled backups, restore drills, service wiring, monitoring and external account independence need separate authorized evidence.

The consolidated verifier is an **offline integration acceptance step**, not completion of production validation or full PT33-B v0.5 release acceptance. Before any commit/push or deployment, review diffs, run tests/regressions, verify docs reflect actual code, and obtain explicit authorization. A separate, reviewed, sanitized Debian collection/evaluation exercise remains outstanding.

## Final milestone acceptance record

For the cumulative evidence, exact command sequence, audit boundaries and release gates, follow [PT33_B_V05_ACCEPTANCE_AND_REBUILD.md](PT33_B_V05_ACCEPTANCE_AND_REBUILD.md). This integrated procedure is the operational reference; the acceptance record is the canonical milestone status and documented exclusions. An accepted local increment is not a production authorization.

## Failure recovery

- Missing/stale/digest mismatch: stop; create new reviewed evidence rather than editing timestamps or digests to bypass validation.
- Source/target mismatch: stop; correct the manifest/evidence pairing and confirm host identity outside the JSON.
- Permission/query failure: retain `failed` or `partial`, request scoped administrator review; never infer absence.
- Existing report path: choose a new output filename; the tool will not overwrite it.
- Collision: investigate naming/ownership, choose a different independent resource proposal, collect new evidence, then reevaluate.

### macOS temporary-directory alias compatibility

On macOS, Python temporary directories may be displayed under `/var/folders/...`,
where `/var` is the operating system's symlink to `/private/var`. The guarded
report writer permits this *specific verified OS alias* (and `/tmp` to
`/private/tmp`) while continuing to reject arbitrary symlinked parent paths,
existing output symlinks, and existing output files. Report creation remains
exclusive (`O_EXCL`) with private file permissions (0600); no overwrite is allowed.
On Debian/Linux, the collector does not permit these symlink exceptions.
