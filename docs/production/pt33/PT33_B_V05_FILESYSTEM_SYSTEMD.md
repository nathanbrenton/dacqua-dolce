# PT33-B v0.5 — Increment 4: bounded filesystem and systemd observations

**Status:** offline-reviewed incremental collector; not comprehensive host verification. No provisioning, production mutation or apply authorization. `ready_to_apply=false`.

## Filesystem probe and limitations

The collector reads the three *proposed* directory roots from the approved, validated business manifest: `instance.service_root`, `instance.config_root`, and `instance.state_root`. It invokes Python's `os.lstat` on each candidate and its ancestors (excluding `/`), collecting **only the proposed path string** when the target already exists or an ancestor is a symlink. This detects a definite existing proposed path and a potentially unsafe alias. It does not traverse symlinks, recursively enumerate `/srv`, inspect file contents, list unrelated business directories, or write anything to the host. No ownership/permission identifiers are currently stored, and parent/child conflicts with unrelated preexisting trees beyond the candidate paths remain unverified.

The `paths` section remains `partial` even when all candidate probes return not found. Failed or permission-denied probes also remain `partial`, with an explicit limitation in `detail`. An empty list is **not** confirmation that the proposed root is free. If no candidate paths were provided by a test fixture, the section is `unsupported`. The offline evaluator treats only positive observations as collisions and never grants clearance from partial paths evidence.

## systemd observations and limitations

Two read-only subprocesses are invoked with fixed argument lists (no shell, no sudo):

- `systemctl list-unit-files --all --no-pager --no-legend --plain` — discovers configured unit-file identifiers, including some disabled and alias references. `--all` broadens enumeration; `--no-pager` prevents an interactive pager; `--no-legend` avoids headings; `--plain` suppresses tree glyphs.
- `systemctl list-units --all --no-pager --no-legend --plain` — supplements with units currently loaded by the manager, which may not have a unit file. This is observational and may race runtime changes.

Only the unit identifier (first column, with recognized unit-type suffix) is retained. No environment variables, unit file contents, drop-in contents, processes or credentials are collected. The two sets are unioned and deduplicated. Failure of one command does not discard positive names from the other; complete lack of successful observation after failure is `failed`. The section **never** becomes `complete`; aliases, generators, transient units, hidden namespace effects and overrides are not conclusively covered. There is no effective-config assertion or safe-to-create finding.

## Local workflow and failure recovery

**LOCAL macOS:** Apply the reviewed source and test files, then run `python3 -m unittest discover -s scripts/pt33 -p 'test_*.py' -v` and `git --no-pager diff --check`. These tests use synthetic output and mocked filesystem metadata: they do not contact Debian production. Preserve the uncommitted work from Increments 1–3.

**PRODUCTION Debian:** No authorization to execute any collection or configuration command is included in this increment. When a separate production read-only collection is approved, follow the existing `PT33_B_V05_DEBIAN_COLLECTION.md` procedure using the correct validated manifest and an unprivileged user. Do not elevate privileges automatically. If evidence is malformed, inaccessible, incomplete, stale, or contradictory, retain the unverified result and investigate offline. Never interpret an empty enumeration as availability.

## Deferred to subsequent milestones

Filesystem ownership/mode provenance, mount namespaces, ancestor ownership, complete service/drop-in/alias resolution, NGINX host and upstream routing, PostgreSQL roles/database metadata and external provider account independence remain unverified. Manual review gates remain mandatory. This increment does not imply a new business can be provisioned safely.
