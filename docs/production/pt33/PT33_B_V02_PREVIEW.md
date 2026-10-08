# PT33-B v0.2 — Inert, offline configuration previews

**Status: local planning prototype — NEVER APPLY generated artifacts.** The v0.1 validator remains unchanged. `render_business_preview.py` imports the exact v0.1 validator and rejects schema/semantic errors before generating illustrative previews.

This renders seven files to a **nonexistent** local output directory: JSON plan and separate non-executable `.txt` previews of systemd, NGINX, environment bindings, and database role design; provider account commissioning checklist; read-first warning. No templates are installable: executable commands, security headers, DB grants, TLS/provider verification and app-specific runtime variables require separate source-level audit and commissioning. Only logical references, never credential values, are rendered.

Usage from project root:

```sh
python3 scripts/pt33/render_business_preview.py \
  --manifest docs/production/pt33/business-manifest.example.json \
  --schema docs/production/pt33/business-manifest.schema.json \
  --inventory docs/production/pt33/offline-inventory.example.json \
  --source-revision "$(git rev-parse HEAD)" \
  --output-dir "$HOME/Desktop/pt33b-preview-sample"
```

An example inventory is **not** a verified host discovery result. Real occupancy and third-party ownership checks are unverified. Any collision with the supplied inventory is refused. An omitted known live resource in that inventory remains a serious risk: never use an offline PASS as a provisioning authorization. Every new business must own distinct registrar/hosting/Proton/Postmark/Cloudflare/Better Stack/AWS/etc. accounts, MFA, billing, credentials and recovery. `ready_to_apply` is always `false`.

Renderer refuses overwrite and existing target paths; outputs are deterministic for identical inputs (including revision), and safe to inspect or discard. No commits, pushes, SSH, providers, filesystem modifications outside the chosen new output directory, migrations or production operations.
