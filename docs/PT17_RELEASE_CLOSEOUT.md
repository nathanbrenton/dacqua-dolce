# PT17 Release Closeout

PT17 is formally closed following successful local validation, GitHub push, exact-revision staging, and production deployment.

## Production checkpoint

- Release family: PT17 — Catalog, Operations, and Responsive Typography Refinement
- Runtime revision: `ce8f92ff2e60e06fc8e6de809f29828695723ce9`
- Production release: `/srv/dacqua-dolce/releases/20260928T072624Z`
- Immediate rollback release: `/srv/dacqua-dolce/releases/20260928T053754Z`
- Deployment backup: `/var/backups/dacqua-dolce/postgresql/dacqua_dolce_20260928T072647Z.dump`
- Release retention count after deployment: 5

The deployment completed with no database migration work and canonical catalog reconciliation reported `total_changes 0`, confirming that PT17's production data state was already aligned with the canonical catalog.

## Delivered scope

### PT17 — Catalog and visual refinement

- Refined public catalog hierarchy and product presentation around the confirmed Harmony, Essence, and Origin families.
- Preserved the boundary that Refine is reserved for a conventional softener line and no unsupported Refine SKU or technical copy is published.
- Removed superseded public-facing Harmony mechanism wording pending authoritative manufacturer documentation.
- Preserved the calcium/magnesium and hardness-removal claim guardrails.
- Reconciled public terminology around Essence automatic backwashing and legacy seed/catalog naming.
- Improved product-card and product-detail visual hierarchy while preserving theme-aware behavior and reduced-motion support.

### PT17.1 — Operations attention dashboard

- Converted the Operations metric area into a compact, actionable dashboard.
- Metrics now navigate directly to the relevant operational section and, where applicable, the first matching item requiring attention.
- Preserved keyboard accessibility, focus treatment, theme behavior, and reduced-motion behavior.

### PT17.2 — Typography readability floor

- Increased the smallest and medium text tiers for readability.
- Preserved the established top display/H1 hierarchy instead of allowing the readability work to enlarge the primary display tier.

### PT17.3 — Semantic typography recipes

- Evolved typography selections from simple font swaps into role-based recipes for body, UI, labels, and data.
- Added deliberate casing, tracking, and weight behavior informed by the site's luxury, culinary, wellness, performance, and technical audience directions.
- Retained Humanist Contemporary / Source Sans 3 as the intentionally unified typography option.
- Typography styling does not broaden product-performance or marketing claims.

### PT17.4 — Shared responsive typography system

- Centralized responsive font-size tiers so all typography recipes share the same hierarchy and breakpoint behavior.
- Typography recipes may change font family, casing, tracking, and weight, but do not independently own responsive `font-size` geometry.
- Large display, section, detail, page, body, UI, small, and micro tiers now have transparent shared sizing behavior across typography choices.
- The large display tier was brought back into the intended visual balance after perceptual inflation became visible in sans-heavy selections.

## Production validation

The PT17 production deployment passed:

- exact staged-source revision verification;
- frontend production build;
- pre-migration PostgreSQL backup;
- Alembic/current-schema validation with no new migration work;
- canonical catalog reconciliation with `total_changes 0`;
- local readiness;
- public `/`, `/account`, and `/health` checks;
- non-public `/readiness`, `/api/docs`, and `/openapi.json` boundary checks;
- HSTS, CSP, Permissions-Policy, X-Content-Type-Options, X-Frame-Options, and Referrer-Policy checks;
- post-switch production validation.

## Durable design rules carried forward

1. Shared responsive typography tiers are authoritative; individual font recipes must not silently change hierarchy size.
2. Large display/H1/H2 tiers remain consistent across typography recipes.
3. Smaller and medium tiers may vary stylistically through font family, casing, tracking, and weight while retaining shared responsive size geometry.
4. Normal controls must remain visually distinct from error states in every theme.
5. Product/public copy must remain inside confirmed client/manufacturer evidence boundaries.
6. Operations attention summaries should be compact and actionable, linking users directly to the work item or section needing attention.

## Next planning boundary

The next large milestone should continue from the client-supported priorities of product/catalog completion and customer purchase readiness. Do not fabricate missing Refine/softener specifications, sizing rules, UV relationships, product documents, or Affinity 24 integration details without authoritative source material.
