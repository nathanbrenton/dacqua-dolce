# PT33-B v0.5 — Increment 5: NGINX hostname evidence

This increment adds **opt-in**, read-only, sanitized hostname observation; it does not certify NGINX effective configuration, nor check upstream names, listen/default_server, socket mapping, overlapping/regex virtual hosts, or file provenance. All observations remain `partial` or `failed` / `unsupported`, never `complete`. The offline evaluator flags exact names and basic `*.example.test` overlaps as *potential collisions*; absence always remains unverified and `ready_to_apply=false`.

## Collection safety

`nginx -T` tests and dumps the expanded on-disk configuration to the collector's process memory. It may include sensitive configuration, which the tool never prints, persists, or returns. Only a strict allowlist of simple ASCII DNS hostname tokens following single-line `server_name` directives is recorded. Variables, regex, complex directives, or malformed content are not accepted. The tool discards stderr, rejects nonzero exits and oversized output, and never saves the raw dump. **Caveat:** invocation still reads sensitive configuration into process memory; only use on a separately approved trusted host. It also does not prove the on-disk configuration matches currently running workers or that all includes were accessible. Review the security policy before enabling this opt-in check.

Without the `--inspect-nginx` flag, the collector performs **no NGINX access** and records `unsupported`. With the flag it runs `nginx -T` using an argument vector (not a shell), with a short timeout and constrained PATH. An unprivileged account may be unable to inspect configuration; this records `failed`, not availability. No `sudo`, reload, service restart, or config mutation is used.

## Commands and recovery

**LOCAL macOS:** Run `python3 -m unittest discover -s scripts/pt33 -p 'test_*.py' -v` using simulated NGINX output. Do not invoke the Debian collector on the Mac.

**PRODUCTION Debian:** Collection is **not authorized by this increment**. If separately approved, use the existing validated manifest and documented collection workflow; `--inspect-nginx` requires explicit additional approval due to transient in-memory sensitive configuration. Never paste `nginx -T` output, NGINX configuration files, or secrets into chat or evidence bundles. If NGINX collection is unavailable or ambiguous, keep it unverified and resolve through a privileged administrator's manual review process.

## Known limits

Static hostname matching cannot establish listener/socket conflicts, default routing, IPv6 behavior, upstream provenance, alias resolution, dynamic reconfiguration, regex semantics, nested includes, or active-runtime equivalence. Wildcards are preliminary collision warnings, not an exhaustive matcher. Do not treat an empty `nginx_server_names` section as clearance. Future increments should address additional sanitized routing metadata and manual review gates before declaring comprehensive host verification.
