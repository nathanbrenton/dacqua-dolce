# PT32 — Inquiry-origin classification

New forms send an explicit origin: `expert_inquiry`, `product_inquiry`, or `recommendation_inquiry`.
The server verifies the origin is consistent with product and recommendation inputs, stores it in PostgreSQL, and uses it for optional operator-subject wording and Operations originating request classification. Expert inquiries may include water-property/recommendation-context details without becoming recommendation-origin inquiries. The declared source is display provenance, not an authorization credential. The existing `quote_requests` entity and formal quote lifecycle remain unchanged.

Migration `b32e10c7a9d4` adds `quote_requests.inquiry_context`, defaulting to `legacy_quote_request` for all existing rows. Historical subject lines and prior communication records are never rewritten. Legacy API clients remain accepted with legacy classification; newer browser requests send their source explicitly.

Local acceptance: apply Alembic to an isolated development/test PostgreSQL database, run backend pytest and Ruff, then build the frontend. Browser-test homepage, product and recommendation paths, and verify actual persisted origin, outbound operator subject and Operations classification. Turnstile, CSRF, acknowledgement cooldown and Postmark stream must remain enforced.

Production: deploy through the exact-revision immutable release process, which takes a pre-migration backup and applies Alembic. Test the three new classifications with controlled inquiries. Do not backfill or alter historical records. Preserve the prior release and database backup for recovery.

Rebuild: restore the authoritative production database; deploy the exact Git revision and apply migrations before enabling traffic. Then recover protected provider settings and validate Cloudflare Turnstile / Postmark independently. See canonical rebuild runbook for full steps.
