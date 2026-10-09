# PT33-B v0.5 — Increment 3: Unix Identity and TCP Binding Observations

**Status:** bounded read-only collector expansion; not comprehensive verification, allocation authorization, or production deployment. `ready_to_apply=false` remains mandatory.

## What is collected

The existing `collect_debian_evidence.py` now invokes four bounded read-only subprocesses without a shell or privilege escalation:

1. `getent passwd` — Name Service Switch (NSS) user identifiers and numeric UIDs, excluding shells, home-directory contents, password fields and other row information from the saved evidence. Both `service_users` and `unix_uids` remain **partial** even when enumeration succeeds: remote identity directories and NSS behavior can prevent exhaustive discovery. Multiple names can legitimately share a UID. This is evidence of a possible identity collision, not a validated identity registry.
2. `getent group` — group names and numeric GIDs, saved separately as `unix_groups` and `unix_gids`. Group membership lists and password fields are discarded. Name and numeric-ID observations remain **partial**; group membership and account/group namespace coupling are not yet evaluated against the proposed business manifest.
3. `systemctl list-unit-files --all --no-pager --no-legend --plain` — bounded existing systemd unit-name observations; no unit environment or secret contents.
4. `ss -H -ltn` — numeric TCP ports (`ports`) plus numeric listening address-and-port tokens (`tcp_bindings`). Examples: `127.0.0.1:8100`, `[::]:443`, `*:8080`. Does not collect process names. The collector does not assert that two binds can coexist, including IPv4/IPv6 dual-stack behavior, wildcard addresses, interface availability, network namespaces, or socket activation. Any observed port is a conservative possible collision, even if the observed address differs from a prospective bind. The result is always **partial**.

Commands return `failed` for nonzero exit, timeout, missing tools and oversized output; malformed entries result in **partial** observations with a warning. No failed/inaccessible source can be interpreted as verified absence. Subprocess calls use fixed argument arrays, eight-second timeouts, a bounded PATH and LC_ALL=C. `getent` may be influenced by host NSS configuration but the collector makes no direct external provider calls.

## Evidence compatibility

The v0.5 evidence contract accepts either the original six sections (Increment 1 and 2 compatibility) or the original six **plus all four** new sections (`unix_groups`, `unix_uids`, `unix_gids`, `tcp_bindings`). It rejects arbitrary extra or incomplete sets. UIDs/GIDs must be unsigned numeric IDs in the documented range; TCP bind entries must have numeric IP or wildcard address and numeric port. An observed binding must have a matching port in the same evidence snapshot; contradictions are rejected. Per-section SHA-256 digests detect accidental edits, **not source authenticity**. The existing evaluator continues to use the original sections for manifested resource collision checks; new identity and bind fields provide review evidence, not automated UID/GID or address-specific clearance decisions.

## Deployment and inspection workflow

1. **LOCAL macOS:** review the source and run `python3 -m unittest discover -s scripts/pt33 -p 'test_*.py' -v`. This executes synthetic fixtures only; do not run the Linux collector on macOS.
2. **PRODUCTION Debian — requires separate user approval:** establish an authorized, read-only collection environment; verify the reviewed source hash, canonical manifest/schema, Python runtime, and availability of `getent`, `systemctl`, and `ss`. Use a non-root account with narrowly scoped permissions. No commands here authorize production execution.
3. **PRODUCTION Debian — approved example only:** `python3 scripts/pt33/collect_debian_evidence.py --manifest docs/production/pt33/business-manifest.example.json --output "$HOME/pt33-observation.json"`. The manifest option points to a validated candidate business; the output option requires a new, private (mode 0600) file and refuses overwrite. Do not use an illustrative manifest as an actual deployment proposal.
4. **LOCAL macOS:** sanitize any approved exported evidence before sharing; run the offline evaluator with `--manifest`, `--evidence`, and explicit `--max-age-hours` according to the business-specific freshness policy. A 24-hour default is a **review policy**, not proof of availability.
5. Verify independent domain registrar, Cloudflare, Vultr, Proton Mail, Postmark, Better Stack, and AWS ownership through their respective dashboards and business recovery controls. This requires separate human approvals and cannot be inferred from a host snapshot.

## Deliberate limitations and recovery

The manifest does not currently declare desired numeric UID/GID or group identifiers, so automatic collision assessment of those is deferred. No filesystem, PostgreSQL, NGINX or complete systemd namespace inspection has been added in this increment. Review networking ambiguity manually and keep unresolved findings unverified. On missing commands, permission errors, malformed output, or stale evidence, investigate the limitation and repeat only an approved read-only observation; **do not escalate privileges automatically or grant clearance**. Never upload production secrets or customer data. See `PT33_B_V05_EVIDENCE_CONTRACT.md` and `PT33_B_V05_DEBIAN_COLLECTION.md` for the canonical base workflow.
