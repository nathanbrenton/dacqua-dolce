# PT33-B — Offline New-Business Planner v0.1

Status: **local-only prototype; not provisioner/renderer**.

The committed PT33-A `business-manifest.schema.json` is validated with the limited, dependency-free subset used by its current schema: `type`, `required`, `properties`, `additionalProperties`, `pattern`, `minimum`, `maximum`, `minLength`, `enum`, `const`, `uniqueItems`, `items`. This is **not a general JSON Schema implementation**; schema changes require corresponding validator review and tests.

Run from repository root:

```sh
python3 scripts/pt33/plan_business.py --manifest docs/production/pt33/business-manifest.example.json --schema docs/production/pt33/business-manifest.schema.json --source-revision "$(git rev-parse HEAD)" --format summary
```

For the full machine-readable plan, omit `--format summary`. Stdout is the output; no files are written.

This prototype supports **new_business only**, with `data.mode=fresh` and `data.seed_profile=null`. It checks the current schema, identifier safety, known D'Acqua resource names, logical secret references, path normalization, hostname, cookies, and selected intra-manifest collisions. It rejects manifest values that directly name D'Acqua production resources. It cannot detect live-host or external-account collisions offline. The output's `ready_to_apply=false` is deliberate and must remain so until a separate approved implementation establishes verified checks.

Every future business has its own domain registrar, hosting, Proton/business-mail, Postmark, Cloudflare, Better Stack, AWS/backup, tax and payment accounts or independently authorized provider accounts, along with its own credentials, MFA, recovery and billing. Required ownership checks are emitted as **unverified**, never asserted as already complete.

No apply command is provided. This script never connects to production, creates accounts, reads secret values, writes configuration, modifies the existing system, or migrates a database. PT33-B's later rendering/apply phases require additional source audit, live resource collision checks, idempotency, strict target path checks, per-business templates and separate approval.
