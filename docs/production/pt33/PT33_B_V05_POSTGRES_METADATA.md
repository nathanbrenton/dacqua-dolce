# PT33-B v0.5 — Increment 6: PostgreSQL metadata evidence

This adds **opt-in** local, read-only PostgreSQL identifier observation to the existing v0.5 host evidence collector. It inspects only the database names from `pg_catalog.pg_database` and role names from `pg_catalog.pg_roles`, using two `SELECT` queries. No table/customer data, password hashes, credentials, role secrets, or database dumps are requested. Collection does not create roles/databases or alter server state.

## Safety and limitations

By default, PostgreSQL access is **disabled** (`unsupported` evidence). The `--inspect-postgres` flag explicitly opts in to using `psql -X -w -A -t -d postgres -c <query>` with an argument list, constrained environment and timeout. `-X` skips `psqlrc`; `-w` refuses password prompts; `-A` and `-t` create machine-readable unaligned, tuples-only output. No host, port, user, password or connection string is accepted as an argument. The collector supplies a limited environment with no `PG*` variables and discards stderr. Authentication may fail; such results are `failed`, not absence. No `sudo`/`su` or privilege escalation is attempted.

**This only checks the default local PostgreSQL connection target and accessible cluster.** Other clusters, sockets, containers, remote servers, access policies, database ownership and role grants are NOT verified. A successful query yields `partial`, not `complete`; a missing name does not clear it for provisioning. Separate manual ownership verification is required before account or resource allocation. Identifier output is bounded and validated; malformed/duplicate results fail closed. A positive exact name match appears as an offline collision. The snapshot always has `ready_to_apply=false`.

## Dependency-ordered workflow

1. **LOCAL macOS:** Run `python3 -m unittest discover -s scripts/pt33 -p 'test_*.py' -v` using simulated `psql` output; do not invoke the Debian collector on macOS.
2. **PRODUCTION Debian:** No collection is authorized by this review package. After **separate explicit approval**, first review the manifest, confirm which cluster is relevant and that the intended Unix account can run read-only queries without password prompts. Use the existing documented evidence collection procedure, adding `--inspect-postgres` only if this is appropriate. Never paste connection strings or credentials into chat.
3. Copy only the sanitized output JSON to the offline evaluation environment using the approved procedure; validate timestamps and report scope and keep all account-ownership gates unverified.
4. If a query fails, note `failed` and resolve through an administrator-led read-only metadata review; do not assume the resource is unallocated.

**Deferred:** explicit multi-cluster inspection, database-to-owner relationships, role memberships/ownership checks, and reconciliation against configured production instances. These require deliberate scope/permission design and tests before v0.5 can be called comprehensive.
