# PT33-B v0.5 — Offline evidence contract, increment 1

**Status:** reviewable development patch, not deployed or approved. This increment introduces the **contract and evaluator**, NOT comprehensive collection. Production host resource verification remains incomplete; `ready_to_apply=false` is mandatory.

## Purpose

A *resource collision* means a requested identifier is already observed on the target host. A *bounded non-observation* means a candidate was not listed in a specific inspection scope; it is **not** authorization to allocate it. A *partial* inspection cannot establish absence. External account ownership cannot be inferred from an operating system snapshot.

The version 2 offline evidence envelope records: `evidence_version=2`, `resource_scope=single_debian_host_read_only`, sanitized `host_id`, proposed `target_instance_id`, declared `source` and `collector_version`, timezone-aware `collected_at_utc`, per-section evidence, an external verification gate, and `ready_to_apply=false`.

Each of six compatibility sections (`service_users`, `systemd_units`, `paths`, `ports`, `database_names`, `database_roles`) has `status`, `values`, `method`, `detail`, and `sha256`. Status is `complete`, `partial`, `failed`, or `unsupported`. `complete` is a reviewer assertion limited to its declared collection method, not an independently validated exhaustive inventory. Collision-positive observations are reported even when coverage is partial. A section marked `failed` or `unsupported` cannot provide inventory values.

SHA-256 covers the canonical JSON values list and detects accidental editing. It is **not** authentication, a digital signature, a chain of custody, or proof that the collector is trustworthy. Contradictory section formats, duplicates, unknown sections, invalid values, digest mismatches, out-of-range ports, false apply readiness, missing external gates, and target-instance mismatches are rejected.

Seven independent-account gates (`domain_registrar`, `cloudflare`, `vultr`, `proton_mail`, `postmark`, `better_stack`, `aws`) must all remain `unverified` in host evidence. Independent verification via separately owned provider accounts is deferred; never record tokens, passwords, customer data, provider account identifiers, or personal information in this envelope.

## Freshness policy

Version 2 defaults to a **24-hour expiry** measured from an exact UTC timestamp. The operator may choose a stricter or looser interval with `--max-age-hours` (greater than zero and no more than 720 hours). This is a conservative **review policy**, not a promise that the host remains unchanged during that interval. Future-dated, timezone-naive, or expired evidence is rejected. Version 1 retains its legacy calendar-day policy and its prior command syntax. Do not use the v1 calendar date as equivalent to a precise inspection time.

## LOCAL macOS — offline assessment only

Run from the repository root after receiving and reviewing a sanitized v2 JSON evidence file (not supplied by this increment):

```bash
python3 scripts/pt33/evaluate_production_evidence.py \
  --manifest docs/production/pt33/business-manifest.example.json \
  --evidence /path/to/reviewed-v2-evidence.json \
  --max-age-hours 24
```

`python3` runs the offline standard-library checker. `--manifest` supplies the proposed business, `--evidence` provides the reviewed JSON, and `--max-age-hours` sets its expiry policy. No SSH, SQL, or provider connection occurs. The evaluator only prints JSON unless `--output` is separately supplied. Never use a guessed manifest or evidence path.

## LOCAL macOS — tests

```bash
python3 -m unittest discover -s scripts/pt33 -p 'test_*.py' -v
```

The tests use synthetic, non-production fixtures. The old v0.4 evidence schema is still accepted through the legacy code path. Preserve the exact outcome semantics of the older contract, including its documented limitations.

## PRODUCTION Debian — intentionally no command in increment 1

Do **not** run a v0.5 collector on production: one is not included in this increment. Do not reinterpret the v0.3 local snapshot or v0.4 manual inventory as v0.5 host evidence. Complete identity, systemd, NGINX, PostgreSQL, bind-address, filesystem, and external-provider collection needs separate guarded implementation and tests before production inspection can be considered.

## Failure handling and next steps

If evidence is missing, unsupported, expired, or malformed, stop and collect a fresh reviewed snapshot once a safe collector exists; never lower a coverage status simply to make a candidate pass. Keep historical raw snapshots segregated and access-controlled. For positive collisions, revise candidate identifiers and reassess offline. For provider ownership, verify the new business's account independently through the relevant dashboard under explicit authorization; do not copy credentials or account IDs into the report. Review source changes and test evidence before any commit, push, or deployment.
