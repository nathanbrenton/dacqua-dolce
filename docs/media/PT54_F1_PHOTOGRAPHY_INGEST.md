# PT54-F1 — Product photography intake specification

**State:** TEST-only foundation. **No existing images, image URLs, database records, commercial options, or live application logic are changed.** Existing product imagery/manifests remain authoritative until a separately reviewed PT54-F2/F3 release.

## Source of truth and workflow

- Editable originals and revised archival masters live **outside the Git checkout** in `~/Desktop/dacqua-dolce_ALL/dacqua-dolce_build-assets/product-photography/`.
- `ingest-drop/` receives original image bytes; files are **never modified or auto-deleted**.
- `staging/` is reserved for F2 previews and image derivatives; F1 does not use it.
- `masters/` is reserved for approved archival revisions; F1 does not copy or rename masters.
- `receipts/` is reserved for future signed/hashed release receipts; F1 writes no receipts.
- `frontend/public/products/media/` remains the website's currently approved source-controlled media. **Do not place raw drop-folder assets here.**
- PT54-F2 will add opt-in ImageMagick transformation/preview/release mechanics. PT54-F3 will add a generated gallery index supporting variable photo counts. Neither exists yet.

## Prospective canonical filename conventions

Lowercase ASCII, underscores between fields, hyphens inside values. Two-digit sequence and version (`01`–`99`). A revision applies to the *same image role and sequence*. Sequence controls deterministic gallery order; role distinguishes system/tank/detail/etc. A filename is an identifier, not a substitute for approved metadata.

| Family | Filename grammar | Example |
| --- | --- | --- |
| Refine / Essence | `{family}_{size}_{material}_{valve}_{style}_{role}_{sequence}_v{revision}.{ext}` | `refine_1-5_neoprene_clack5_archetype_system_01_v03.png` |
| Harmony | `harmony_{size}_{material}_{role}_{sequence}_v{revision}.{ext}` | `harmony_1-5_stainless_pureline_02_v01.png` |
| Origin | `origin_{variant}_{role}_{sequence}_v{revision}.{ext}` | `origin_remineralization_detail_01_v02.png` |

Allowed values:

- `family`: `refine`, `essence`, `harmony`, `origin`.
- `size`: `1-5`, `2-0` (cubic feet); must be applicable to the physical system, **not** a statement that a size is approved for sale.
- `material`: `stainless`, `neoprene` (photo finish/jacket).
- `valve`: `clack3`, `clack5`, `performance` (identifies visual hardware, never a commercial option at F1). Existing `clack` filenames are legacy/ambiguous: **do not automatically relabel** as Clack3 or Clack5.
- `style`: `archetype`, `realistic`; applicable only to the valve/tank family photographs in this schema.
- `variant` for Origin: `standard`, `remineralization`.
- `role`: `system`, `tank`, `valve`, `brine`, `pureline`, `cartridge`, `detail`, `angle`, `hookup`, `membrane`, `faucet`. Roles are labels, **not** permission to combine arbitrary photos or configurations.
- `sequence` / `revision`: decimal `01` through `99`.
- `ext`: `png`, `jpg`, `jpeg`, `webp`, `tif`, `tiff`. F2 will decide which sources can be accepted for archival master generation.

Photo filenames must **not include mutable SKUs, price, stock, quote status, or public marketing claims**. Future caption, alt-text, roles, approval, credit, image resolution, checksums, and audit events should live in generated metadata/receipts rather than expanding filenames. Logo and backgrounds will use a separate future schema.

## Safety and approval boundaries

1. F1's `init` command creates missing directories only under the existing `dacqua-dolce_build-assets` library. It never overwrites a file.
2. F1's `scan` command scans prospective **flat** `ingest-drop/` entries and existing legacy JSON manifests. It reports anomalies but never fixes or moves data. Photo thumbnails are not generated.
3. No implicit fallback from `clack3` to `clack5`, no false approval of Harmony 2.0, no guessed manufacturer SKU, no silent media replacement.
4. Multiple revisions of the same photo slot and identical content under different filenames are surfaced for human review; F1 never selects a winner.
5. Legacy files remain valid even when their names do not match new grammar. The legacy manifests use inconsistent keys (`website_webp` / `website_lossless_webp` and `thumbnail_webp` / `thumbnail_lossless_webp`), so future migration must normalize them explicitly, non-destructively.
6. Existing fixed media registries and Origin-specific gallery logic remain in use. F1 does not change customer-facing photos, their order, or commercial behavior.
7. Reports include original names, candidate dimensions and SHA-256 hashes; treat them as internal records. Reports are created exclusively, never overwritten.

## TEST (macOS) — Usage

Run from `~/Desktop/dacqua-dolce_ALL/dacqua-dolce` after installing F1's new repository files. Use Python 3; ImageMagick 7 is optional for format and dimensions but installed in the inventoried TEST environment.

```bash
python3 scripts/media/pt54f1_media.py init
python3 scripts/media/pt54f1_media.py parse --filename refine_1-5_neoprene_clack5_archetype_system_01_v03.png
python3 scripts/media/pt54f1_media.py scan
python3 -m unittest discover -s scripts/media/tests -p 'test_pt54f1_media.py' -v
```

If `init` has not been used, `scan` still audits existing legacy manifests and reports that the new intake folder is absent. `scan --no-write` prints its structured JSON report without writing a file. Default reports are written to `~/Desktop/dacqua-dolce_ALL/dacqua-dolce-pt54f1-scan-<timestamp>.json`.

**PROD:** No PT54-F1 command is intended to run on production. The production revision remains `9e451f83de59e6f10ac3963c2a307e6b9d82e683` until a separate approved release.
