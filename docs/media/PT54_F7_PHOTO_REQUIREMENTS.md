# PT54-F7 — Photo requirements reminders in local Media Manager

**TEST only.** The Photo Requirements quick-reference panel appears immediately above the upload/drop area in the local Media Manager (`http://127.0.0.1:18174/`). It is always visible; the naming and detailed processing rules are expandable. This is guidance only: all F1/F2/F4 server-side validation remains authoritative and unchanged.

## Actual F1/F2/F4 constraints

- Source types: `.png`, `.jpg`, `.jpeg`, `.webp`, `.tif`, `.tiff`. The UI permits at most 64 MiB per upload. Folder-based intake is capped at 256 MiB, with the actual image at least 16×16 px and at most 50 megapixels.
- Preferred portrait originals: 1122×1402 px or larger at approximately 4:5, **not an enforced minimum**. More pixels or alternative aspect ratios are accepted within the safety limits. The processor **does not upscale or crop**.
- Website derivatives: PNG and lossless WebP, contained within 1122×1402 px. Thumbnails: PNG and lossless WebP, contained within 384×480 px. Aspect ratio is retained.
- Each prepared source yields an unchanged master, 4 image derivatives and a JSON manifest.
- Metadata-driven filenames use family-specific rules and two-digit sequence/revision. Product variants, photographed valves and image style are descriptive metadata, not pricing/inventory selections.
- Preparation is separate from TEST publication; PROD is not touched.

## TEST validation

Restart the local Media Manager after installation; confirm the panel renders above the file drop box. Expand its details and verify the family-specific examples. The existing Current Library and thumbnail Caption Editor remain unaffected.

No Git commit, push, migrations, server upload or product image changes are performed by this patch.
