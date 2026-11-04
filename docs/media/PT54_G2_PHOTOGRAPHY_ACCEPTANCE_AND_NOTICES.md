# PT54-G2 — Photography acceptance and two customer-facing notices (TEST)

## Scope
- **No new photography generation or transcoding.** The approved G1/G1.1 set is reused.
- All 36 sources, all 144 published image derivatives, and all 24 active galleries are validated with the G1 checksums.
- Refine/Essence/Harmony historical photo paths are not selected while AI placeholders are active. Their physical files remain untouched and recoverable.
- Origin RO and individual fitting/hookup photo assets remain untouched.
- Aesthetic Lab retains AI placeholder photography as the available default; actual photography remains unavailable until photographs exist and are separately approved.
- No data migration, order, quote, inventory, or commerce modifications.

## Copy, placement, and ownership

**Product image disclaimer** — displayed directly after the product gallery on *all* product detail pages, including Origin, regardless of active gallery source.

> Product images may vary slightly from the actual product received. Variations in appearance, color, finish, or component design may occur without affecting the product's intended functionality or performance.

**PureLine filter maintenance** — displayed once on Harmony product detail pages after the cartridge configurator (not repeated in multiple visible sections).

> **Important Maintenance Notice:** PureLine filter cartridges must be replaced according to the recommended maintenance schedule. Failure to replace cartridges in a timely manner may cause certain filter media to soften, deteriorate, or disintegrate, potentially resulting in plumbing blockages, equipment malfunction, or damage to the plumbing system.

Exact text is centralized in `frontend/src/components/catalog/productNotices.json`. Changes to warranty, technical claims, or manufacturer recommendations require their own technical and legal approval before PROD. The G2 test receipt specifically records that this review remains pending; **it does not authorize a production deployment**.

## Acceptance

Run `python3 scripts/media/pt54g2_acceptance.py audit` to verify the actual G1/G1.1 ledger, published media, gallery selections, and retained legacy folders. Run `python3 scripts/media/pt54g2_acceptance.py record --accept-visual-review` to create a timestamped, offline, TEST-only acceptance JSON under `~/Desktop/dacqua-dolce_build-assets/product-photography/acceptance/`. Recording requires an explicit operator assertion of visual approval.

There is **no destructive cleanup** in G2. Keeping unused historical gallery images physically available guards against unknown references and supports rollback. Physical deletion would require a separately reviewed reference scan, archival verification, and PROD plan after release.

## Release boundary
No Git add, commit, push, deployment, or PROD changes are performed by this kit. G2 adds code/copy to TEST only. Existing PROD remains on its currently deployed revision. Do not present the maintenance-damage statements as manufacturer-approved until independently verified.
