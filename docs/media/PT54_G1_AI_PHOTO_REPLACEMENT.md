# PT54-G1 — AI placeholder photo replacement (TEST only)

## Source contract

Expected input: 36 exact PNG files from `~/Desktop/new-photos/{refine,essence,harmony}/`.
All are 1122 × 1402 px. The checksum-locked ledger is
`scripts/media/pt54g1_sources.json`. Filenames are preserved exactly.

`chrome` is a **source filename attribute** mapped explicitly to the
storefront's established `stainless` presentation value; the commercial
configuration data is not changed. `pass-through` remains a technical/internal
Harmony media identifier, not customer-facing product copy.

## Safety gates and operation

From TEST repository root:

1. `python3 scripts/media/pt54g1_replace.py plan` — validates all files,
   sizes, dimensions, names, exact SHA-256, 24 gallery mappings, and reports
   the four cross-family duplicate photographs. Nothing is written.
2. `python3 scripts/media/pt54g1_replace.py prepare --acknowledge-cross-family-duplicates`
   — only after reviewing duplicate reports. Generates a unique fixed-name
   immutable staging batch under the local offline asset library. Nothing in
   the website changes yet.
3. Open the printed `review.html` with `open <path>`. Review all 36 photographs
   and confirm Essence/Refine duplicates are acceptable.
4. `python3 scripts/media/pt54g1_replace.py activate --acknowledge-cross-family-duplicates`
   — archives original bytes, installs PNG/WebP and thumbnails into
   `frontend/public/products/media/ai-placeholders/`, and atomically switches
   the versioned `photoSetIndex.json` last.
5. `python3 scripts/media/pt54g1_replace.py verify` — checksum-verifies all
   36 archival masters, 144 derivative files, and 24 selected galleries.
6. Run the patch's `apply.py audit`, then review the browser galleries.

Operations are repeat-safe where applicable, and the script refuses conflicting
existing destinations. An interrupted prepare leaves no partially published
index. An interrupted activation can be retried using the same reviewed batch.

## Display behavior

The AI placeholder set supersedes **all historical gallery selections** for
Refine, Essence, and Harmony; the old files are not selected as fallback photos
once this set activates. The original media files stay in their existing repo
locations for safe rollback until a **separately reviewed cleanup**. Origin
RO systems and dynamic installation fitting images are unchanged.

There are no new Clack or Realistic/Archetype variants in the supplied set.
Those selectors are disabled in the footer's Aesthetic Lab while this AI set
is active. Performance remains the default. The future `product-photo` source
option is present but disabled until actual photographs are supplied and
reviewed. None of these controls enter pricing, orders, quotes, or inventory.

## Maps

- Refine: 4 size/finish configurations; each has complete system, tank-only,
  brine-tank front, and brine-tank side galleries (4 images each).
- Essence: 4 size/finish configurations; one complete-system photo each.
- Harmony: 16 size/finish/Pureline configurations; bare system has one photo,
  attached Pureline 1/2/3 have complete system, standalone tank, and
  front/rear housing photos.
- Origin: existing galleries unchanged.

## Duplicate content review

**Four Essence sources are byte-identical to Refine tank-only sources** with
matching size/finish. This is detectable without viewing their pixels. The
pipeline refuses preparation and activation unless the operator explicitly
acknowledges those four pairs. No automatic assumption that the two families
are the same physical equipment is made.

## Production boundary

No PROD deployment, Git add/commit/push, database migration, or catalog seed
change is part of this patch. Preserve the current production rollback release.
