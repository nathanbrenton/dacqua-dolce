# PT54-F5 — Current TEST Library Viewer

The standalone Media Manager at `http://127.0.0.1:18174/` includes a **Current TEST library** section above the intake workflow.

- Read-only; no media files are modified, replaced, copied, transcoded, committed or published.
- Product-family and exact configuration selectors include **48 Refine / Essence / Harmony** configurations from the website's static `PHOTO_REGISTRY` and **two Origin** galleries from its separate `ORIGIN_GALLERIES`.
- The viewer applies approved F3 `publishedPhotoIndex.json` revisions to the same slots the application uses.
- Each gallery image is shown as a thumbnail with an optional full-resolution local preview. Missing files are flagged.
- The viewer reads only media URLs statically selected by the local TEST gallery registry. It does not expose arbitrary filesystem paths, track every historical derivative, or include dynamically selected customer fitting images.
- This is NOT an inspection of currently deployed PROD: PROD was rolled back to revision `9e451f8`, while the local TEST repository is at `aca47e6` plus uncommitted E/F work. A direct production-media inventory would require separately verifying the production release and its assets.

## Use

1. Start `python3 scripts/media/pt54f4_manager.py` in the local TEST Terminal.
2. Open `http://127.0.0.1:18174/`.
3. In **Current TEST library**, filter by product family, choose a configuration, and click any thumbnail for full resolution.
4. Close the preview, then use the existing **Name & ingest** workflow to prepare polished replacements.

No network access to the public website is used. The viewer uses local approved image definitions and files only. It never invokes the F3 publisher.
