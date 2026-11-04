# PT54-F2 — Review-only photo preparation

**TEST only. No publishing, database updates, logo/background changes, Git commits, or deployment.**

F1 remains the read-only intake scanner. F2 introduces an isolated *preparation batch* after sources have been placed in `~/Desktop/dacqua-dolce_build-assets/product-photography/ingest-drop/` and named according to F1. Existing media, legacy filenames, and all 52 legacy JSON manifests stay unchanged.

## Deliverables per accepted source

F2 creates a unique `staging/batch-<UTC>-<random>/items/<asset-stem>/` containing:

1. `master/<original-filename>` — **byte-for-byte copy**, retaining the approved archival original untouched in the intake folder.
2. `website/<stem>.png` — PNG, aspect preserved, bounded to **1122×1402**, no upscaling or cropping.
3. `website/<stem>.webp` — **lossless WebP**, aspect preserved, max 1122×1402.
4. `thumbnails/<stem>.png` — PNG, max **384×480**.
5. `thumbnails/<stem>.webp` — lossless WebP, max 384×480.
6. `manifest.json` — SHA-256, dimensions, photo identity, proposed destinations and collision warnings. All five media files are verified by checksum.

Each batch also includes `batch.json` and `review.html` (a static, offline browser review sheet). **No file inside the staging batch is automatically published, approved, moved to `masters/`, or copied into the website.** The original input file is never renamed or deleted. Publication and variable-length galleries are deferred to F3.

Images may be smaller than the maxima; F2 does not distort or enlarge them. `-auto-orient` honors EXIF orientation. Web derivatives remove embedded EXIF, IPTC and XMP tags while retaining other profiles; review on the target browser remains mandatory. There are no filters, stylistic changes, annotations, or watermarks.

## Local TEST commands

After installing PT54-F2 and dropping at least one suitably named original into `ingest-drop/`:

```bash
cd ~/Desktop/dacqua-dolce &&
python3 scripts/media/pt54f1_media.py scan --no-write --summary-only &&
python3 scripts/media/pt54f2_prepare.py plan &&
python3 scripts/media/pt54f2_prepare.py prepare &&
python3 scripts/media/pt54f2_prepare.py verify-latest
```

Open the printed `review.html` path using Finder or `open <full-review.html-path>`. Use `--filename refine_1-5_neoprene_clack5_archetype_system_01_v03.png` on `plan` or `prepare` to process one selected source rather than every source in the intake folder. For explicit verification use `verify --batch <staging/batch-...>`. Repeated `prepare` creates a *new* independent review batch; it does not overwrite another batch.

## Safety and handoff boundaries

- An empty intake folder is not an error in F1; **F2 preparation correctly stops** until at least one real source photo is available. Installer tests generate synthetic images only in temporary directories.
- Source filename, format, dimensions and SHA-256 are inspected before any transformation. Only 16px+ images up to 50 MP and 256 MiB are accepted. Symlinks, nonfiles, misleading extensions, duplicate content and competing revisions in a batch are rejected. A single file can be chosen explicitly for revision conflicts.
- Review and filename compliance do **not** establish supplier provenance, product authenticity, availability or commercial approval. Specifically, `clack3`, `clack5` and `performance` are photographic metadata only; Harmony 2.0 isn't authorized by photographs.
- `manifest.json` **proposes** destinations under `frontend/public/products/media/<family>/generated/` and archival `masters/<family>/`; any destination collision is flagged for manual resolution. No automatic replacement is performed. The existing registries and quote rules remain untouched.
- `verify` checks derivative hashes, master/source integrity at preparation time and rejects unexpected staged files or symlinks.
- This stage emits **no customer-facing gallery changes**. F3 must create a reviewed publication and generated variable-length gallery registry with explicit existing-asset coexistence, approvals and rollback.

**PROD** remains on `9e451f83de59e6f10ac3963c2a307e6b9d82e683` after the approved rollback. No F2 commands belong on PROD.
