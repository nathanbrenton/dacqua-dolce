# PT33-B v0.5 — Canonical acceptance, rebuild and independent-business gates

**Status (2026-10-08, America/Los_Angeles):** local PT33 implementation verified; **NOT** production-verified, deployment-authorized or approved for commit/push. This is a planning and sanitized-evidence release candidate, not a production installer. Every collector and evaluator output must retain `ready_to_apply=false`.

## Architecture and scope

- A forkable shared application/tooling codebase supports **separately deployed business instances**. Each business is a distinct host/environment, database and runtime identity, domains, secrets, recovery ownership and third-party provider administration. This is not an account on a multi-tenant D'Acqua Dolce deployment.
- Manifest values are proposals, not reserved resources. Positive evidence of an existing resource is a conflict. Missing observations from partial/failed/unsupported coverage **never** prove availability. Even bounded `complete` observations are not permission to provision.
- Host evidence is **not authenticated attestation**; section SHA-256 digests detect alterations to inventories but do not authenticate the collector, SSH transport, privileged identity or host. Freshness is a policy threshold, not a guarantee of current availability.
- Never reproduce customer records, production secrets, full NGINX configuration, PostgreSQL authentication material, live mailboxes, backup keys or provider credentials in an exported snapshot, release package or public repository.

## Acceptance matrix — evidence actually available

| Gate | Observed status | Remaining requirement |
|---|---|---|
| PT33 incremental macOS unit/integration suite | **PASS: 86/86** after Increment 7 macOS report-path fix | Re-run at final commit candidate and capture its exact revision |
| Isolated reconstructed PT33 suite | **PASS: 86/86** | Recheck equivalence to the actual Mac working tree during review |
| macOS report path security | **PASS**: OS `/var` alias and overwrite/symlink negative tests | Preserve these tests in future changes |
| General backend pytest | **NOT PASSED / INCONCLUSIVE** | Run on a deliberately isolated, migrated, initialized test database; don't use production or existing valuable development data |
| PostgreSQL-backed backend test prerequisite | **MISSING LOCALLY**: PostgreSQL 17 installed but `127.0.0.1:5432` not responding; Homebrew service inactive | Separate approval for creation of a disposable database and schema migration, with verified connection identity |
| Debian host v2 evidence | **NOT COLLECTED** | Obtain separate explicit approval, review command set, output location, privileges, privacy and host identity |
| NGINX and PostgreSQL opt-in metadata inspection | **NOT AUTHORIZED** | Separate scope review; avoid leaking raw NGINX output or authentication data |
| External provider independence | **UNVERIFIED** | Verify each account, recovery, billing and alert authority with business administrators |
| Commit/push/deployment | **NOT AUTHORIZED** | Explicit user approval after gates and review |

### Backend regression explanation

The system `python3` lacked `pytest`; the repo's `backend/.venv/bin/python` has it. Running without `DACQUA_DATABASE_URL` produced 35 import-time configuration errors. A later diagnostic used `DACQUA_ENVIRONMENT=test` with `sqlite+pysqlite:///:memory:` and collected the suite, but failures included `no such table: users`, `products`, `communication_threads`, and HTTP 403 registration responses. The SQLite test attempt **must not** be represented as an accepted backend regression. `backend/tests/conftest.py` sets test environment only; it does not migrate/init tables. PostgreSQL is installed but not running on the local default port. Do not start services, migrate databases, fabricate fixtures or replace a real URL without a distinct authorized test plan.

## Rebuild-grade dependency map

Follow these references in order; the incremental technical notes are retained as source-level reference, not competing final procedures.

1. [PT33_A_PROVISIONING_SPEC.md](PT33_A_PROVISIONING_SPEC.md) — desired business isolation and resource boundary.
2. [PT33_B_OFFLINE_GENERATOR.md](PT33_B_OFFLINE_GENERATOR.md), [PT33_B_V02_PREVIEW.md](PT33_B_V02_PREVIEW.md), [PT33_B_V03_HOST_EVIDENCE.md](PT33_B_V03_HOST_EVIDENCE.md), [PT33_B_V04_PRODUCTION_EVIDENCE.md](PT33_B_V04_PRODUCTION_EVIDENCE.md) — historical phases and compatibility.
3. [PT33_B_V05_EVIDENCE_CONTRACT.md](PT33_B_V05_EVIDENCE_CONTRACT.md) — evidence format, scoped freshness/digests and failure states.
4. [PT33_B_V05_DEBIAN_COLLECTION.md](PT33_B_V05_DEBIAN_COLLECTION.md), [PT33_B_V05_IDENTITIES_NETWORKING.md](PT33_B_V05_IDENTITIES_NETWORKING.md), [PT33_B_V05_FILESYSTEM_SYSTEMD.md](PT33_B_V05_FILESYSTEM_SYSTEMD.md), [PT33_B_V05_NGINX_ROUTING.md](PT33_B_V05_NGINX_ROUTING.md), [PT33_B_V05_POSTGRES_METADATA.md](PT33_B_V05_POSTGRES_METADATA.md) — limited source-level collector behavior.
5. **[PT33_B_V05_INTEGRATED_VERIFICATION.md](PT33_B_V05_INTEGRATED_VERIFICATION.md)** — canonical dependency-ordered offline operator procedure, with separate unapproved Debian and provider phases.
6. This file — actual acceptance status, remaining gates and acceptance handoff.

## LOCAL macOS — permitted validation (no production or database service)

Use the actual checkout and do not stage, commit, push or deploy while review is incomplete:

```bash
cd "$HOME/Desktop/dacqua-dolce"
python3 -m unittest discover -s scripts/pt33 -p 'test_*.py' -q
git --no-pager status --short --branch
python3 scripts/pt33/plan_business.py --help
python3 scripts/pt33/verify_business_resources.py --help
```

Inspect `scripts/pt33/evidence_contract.py`, `collect_debian_evidence.py`, `evaluate_production_evidence.py`, and `verify_business_resources.py` alongside the exact manifest schema and new-business example. Keep private evidence/reports outside the public repository. A safe report filename must be new; existing files are never overwritten.

## Production Debian — pending *separate* approval

**Do not execute any production command based solely on this document.** Before proposing commands, confirm the production host alias and identity, current approved scope, user and permissions, manifest identity, collector version, output directory with free space and strict permission handling, and a secure sanitization/transfer workflow. Run collection only after affirmative authorization. Optional `--inspect-nginx` and `--inspect-postgres` need separate express consideration; both are disabled by default. The collector uses `getent`, `systemctl`, `ss`, and bounded path `lstat`; PostgreSQL names use `psql -X -w` with an intentionally constrained environment and may fail authentication. Treat any error, missing provider proof or contradictory data as **unverified**.

Keep raw server inventories private. Authenticate the host separately from the JSON labels, and record source/date, operator identity, tool revision, approved scope and the sanitization signoff; do **not** claim these fields are already authenticated by the snapshot schema. Re-evaluate offline from a reviewed fresh v2 snapshot using the integrated procedure. Never translate this evaluation into provisioning authorization.

## External and unresolved technical gates

Independent ownership review must explicitly include domain registrar, Cloudflare, Vultr, Proton, Postmark, Better Stack and AWS, with account recovery, billing, notification and offboarding separation. Multiple API tokens in a shared account are not independence.

Do not claim exhaustive NGINX effective-routing coverage (`default_server`, `listen`, regular expressions, upstreams, includes and runtime load differ); exhaustive PostgreSQL clusters/ownership/privileges; numeric Unix UID/GID manifest guarantees; all NSS/systemd sources; full TCP namespace and IPv6 coexistence; complete filesystem permissions/mount topology; or verified backups, restore drills, DNS/TLS, firewall and monitoring. These remain explicit manual gates or future enhancements.

## Stop conditions and completion criteria

Stop on collisions, unknown source identity, schema/freshness/digest mismatches, ambiguous host, missing coverage, unsafe output path, unauthorized provider access, or request for secret material. Use a different proposed resource and freshly collected authorized evidence rather than changing digests/timestamps to obtain a favorable answer. The milestone can only be called **locally PT33-accepted** with the 86 passing tests; **production-verified** requires separately approved/validated host and provider evidence; **releasable** requires accepted backend regression or documented exception plus explicit user authorization to commit/push. `ready_to_apply=false` remains a hard boundary in all cases.
