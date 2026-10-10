# PT36 — Supplemental privileged metadata observation (review only)

## Status

Prepared locally, **not yet exercised on production**. Requires separate review and operator approval before transfer or execution. No provisioning authorization; `ready_to_apply=false` in every produced report.

## Architecture

The script itself **must run as an ordinary Linux user**, not as root. It uses exactly three fixed, noninteractive read-only commands: `sudo -n /usr/sbin/nginx -T` and two `sudo -n -u postgres /usr/bin/psql -X -w -A -t -v ON_ERROR_STOP=1 -d postgres -c ...` catalog-name queries. The only SQL statements select `datname` from `pg_catalog.pg_database` and `rolname` from `pg_catalog.pg_roles`.

NGINX `-T` parses/dumps on-disk configuration; its stdout **may contain sensitive data**. Raw stdout and stderr are captured **only in subprocess memory**, never printed, persisted or exported; stdout is capped at 2 MB and the process times out at 12 seconds. In exceptional failures, OS swap/crash dump/process introspection and externally configured auditing remain outside this script's guarantee. Treat the privileged read as sensitive. The parser exports only conservative literal `server_name` DNS identifiers. Complex/regex/default/multiline statements are not resolved.

The report contains the observed NGINX hostnames and PostgreSQL database/role names. Those **are internal infrastructure identifiers** and must remain in the private operator directory, outside Git, shared only after review and redaction. Command failures are `failed`, not evidence of absence. Successful enumeration stays `partial` due to possible other clusters, privilege boundaries, routing precedence, and active-versus-on-disk differences.

The helper deliberately does not write a PT33 v2 evidence file and **must not be merged into the initial unprivileged PT33 snapshot** without a separately reviewed provenance-preserving integration. It does not authorize business allocations, changes to services, privilege grants, or deployments.

## Local validation

`python3 -m unittest discover -s scripts/pt36 -p 'test_*.py' -q` runs mocked tests only. This is not proof of correctness on the production host. Before any execution, review source, sudo policy, permissions, and destination. Do not modify sudoers merely for this exercise.

## Production acceptance gates

1. Explicitly authorize the sensitive in-memory NGINX dump and PostgreSQL catalog-name queries.
2. Confirm checksums of the exact script reviewed; use a private 0700 user-owned directory, with a unique output filename.
3. Execute **only as ordinary `n8`**, without changing service configuration. The `--acknowledge-sensitive-read` flag is an operator acknowledgement, not a substitute for authorization.
4. Review status-only stdout; keep the private mode-0600 report on-host until reviewed for safe transfer.
5. Review failures without escalating script execution to root; do not weaken authorization boundaries.

Do not include raw NGINX configuration, SQL results, or raw report contents in chat or public version control.
