# PT54-F3 — Reviewed photography publication and variable galleries

**TEST / macOS only.** This milestone is deliberately not connected to Operations or production. No database migrations, price changes, Git staging/commits/pushes, or remote actions.

## Compatibility

This is an additive layer above the approved PT53 registry. Initially `publishedPhotoIndex.json` has no entries, so all existing photography remains unchanged. Refine, Essence, Harmony, and Origin support additional, a variable number of approved gallery photographs. A reviewed `system_01` or `tank_01` image replaces that gallery position; the previous approved photo remains its runtime fallback and all original files remain on disk.

When F2 produces a new review batch, use:

```bash
python3 scripts/media/pt54f3_publish.py plan --batch '/full/path/to/staging/batch-...'
python3 scripts/media/pt54f3_publish.py publish --batch '/full/path/to/staging/batch-...' --approve 'batch-...'
python3 scripts/media/pt54f3_publish.py verify
```

`--approve` must exactly match the batch folder name. **Do not publish before visually reviewing `review.html`.** The publisher will verify F2 hashes and reject target collisions, reused photo revision slots, unsafe paths/symlinks, or Clack3/Clack5 mixing within one gallery configuration. It copies F2 assets to the archived masters and generated website directories and updates the source-controlled index. All writes stay local; inspect `git diff` and the receipt before committing/deploying.

## Identity and selection

- `refine` / `essence`: `family:size:material:clack|performance:archetype|realistic`. The F1 valve name `clack3` or `clack5` explicitly supplies the photographed model; the app continues to use the global visual `clack` setting. The first published Clack variant for a configuration establishes its model; publishing photos of the other Clack model to that same configuration is rejected, never mixed automatically.
- `harmony`: `harmony:size:material:pass-through:0`. Approved images apply to the base configuration; Pureline-combination hero photography stays unchanged. No invented valve or photo style.
- `origin`: `origin:DD5RO` (standard) or `origin:DD6ROAE` (remineralization). Existing Origin galleries remain intact until individually overridden.

For each config, photo role + 2-digit sequence selects a gallery position; the highest approved version wins. More positions can be added without changing React source. Fitting photographs chosen interactively remain the final gallery item, unless they have their own published gallery positions. A new `hookup` photo in the published collection is informational and does not change commercial hookup selection.

## Safety and history

- F2 original intake files are never moved/deleted; a byte-identical archival master is written only if its path doesn't already exist.
- Existing website media are never overwritten; each new publication has a unique revisioned name.
- Previous index entries remain as release history; old images remain in the repository.
- A receipt is stored in external `product-photography/receipts/` (not Git). If a write fails before final publication, newly copied files are removed and the prior index is restored.
- To undo an already committed publication, use Git to revert the corresponding index change or create a new reviewed higher-version image. Do not delete files from production releases. No CLI unpublish/delete action is included in F3.
- `verify` checks index schema, paths, duplicate revision slots, model consistency, and the existence of all referenced website media.

No new images are required to install or validate F3. The tests use synthetic images and temporary directories outside the real catalog.
