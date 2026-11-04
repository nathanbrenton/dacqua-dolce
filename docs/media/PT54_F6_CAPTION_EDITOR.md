# PT54-F6 — Gallery Thumbnail Caption Editor

The Current TEST Library in `http://127.0.0.1:18174/` now includes an editable thumbnail subtitle area. Choose a product configuration and a thumbnail, edit the caption, choose its scope, and save. Preview the same configuration in the local Vite product page.

- **This configuration only** adds/edits an override for one exact family/size/material/valve/style or Origin SKU. This takes precedence over any family-wide caption.
- **Entire product family** updates any selected image with that same *photo ID* in the family. For example, `tank` covers Refine tank photos, not the separate `brine` slot. Individual configuration overrides still take precedence.
- **Remove this override** clears the selected scope's entry, restoring its inherited or original caption.

The authoritative deployable source is `frontend/src/components/catalog/photoCaptionOverrides.json` (schema version 1). It is loaded by `productMediaRegistry.ts` after the approved-image overlay is resolved. No image is reprocessed; SKU, pricing, inventory, alt text, and database contents are unchanged.

Each save creates a copy of the prior JSON in `~/Desktop/dacqua-dolce_build-assets/product-photography/receipts/caption-backups/` and atomically updates the tracked TEST JSON. Only the JSON (and F6 source changes) must be committed for the captions to travel to PROD in the *next explicitly approved release*. Browser changes in PROD will not appear until deployment.

Security: local loopback-only server, CSRF and Origin checks for POST, allowlisted selected-gallery configuration and photo identifiers, optimistic checksum-based collision detection, plain text maximum 96 characters, no symlinks or arbitrary file writes. Existing unedited captions remain unchanged.

The Current Library is sourced from local TEST registry, not from the rolled-back live PROD revision. Dynamic fitting image previews are handled separately and are not yet listed in Current Library.

### Validation

```text
python3 -m unittest discover -s scripts/media/tests -p 'test_pt54f*.py' -v
node --check scripts/media/pt54f4_ui.js
cd frontend && node --test tests/pt54f6-captions.test.mjs && npm run build && npm audit --audit-level=moderate
```
