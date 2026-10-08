# PT32 Phase B — Turnstile commissioning

Managed Turnstile is **commissioned in production** for public Support and Quote/Inquiry requests. The template defaults OFF for safe *new* environments; deployed production has both build-time site key and backend runtime secret configured. Never enable backend verification before deploying a site-key-enabled frontend build.

- Cloudflare: register production hostname `dacquadolce.com`, Managed widget; retain secret only in protected server environment.
- Frontend build: `VITE_TURNSTILE_SITE_KEY` (public key, safe to embed). Rebuild frontend after setting.
- Backend runtime: `DACQUA_TURNSTILE_ENABLED=true`, `DACQUA_TURNSTILE_SECRET` (protected), `DACQUA_TURNSTILE_EXPECTED_HOSTNAME=dacquadolce.com`.
- Siteverify: server-side POST; hostname + action checked; network errors fail closed. Tokens are never logged.
- CSP: live NGINX must allow `https://challenges.cloudflare.com` in `script-src`, `frame-src`, and `connect-src`; updating a checked-in template does **not** update `/etc/nginx/sites-available/dacqua-dolce.conf` automatically. Apply with reviewed backup, `nginx -t`, and reload.
- Support honeypot remains first and is deliberately returned as a success without verification; no database record is generated.
- Reused/expired tokens are rejected by the provider; the frontend resets the widget after each attempted submission. Verify retry UX manually before production enablement.
- Test local and production provider commissioning separately. Do not commit secrets or enable production settings in Git.
- Rollback: disable `DACQUA_TURNSTILE_ENABLED` only as an explicitly approved operational break-glass action; otherwise restore last known-good exact release.
