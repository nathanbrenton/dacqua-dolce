# PT54-F4 — Local TEST Media Manager

## Scope

F4 is a standalone **local macOS** web interface. It listens **only on 127.0.0.1** and operates on:

- `~/Desktop/dacqua-dolce_ALL/dacqua-dolce/` — the TEST source tree;
- `~/Desktop/dacqua-dolce_ALL/dacqua-dolce_build-assets/product-photography/` — the external archival/photo library.

It does **not** run inside FastAPI, connect to production, deploy, alter a database, stage or commit Git, change pricing/inventory, or access the public Operations panel. No updated product photos are necessary to install or open it.

## Start and stop

From the local TEST macOS Terminal:

```sh
cd ~/Desktop/dacqua-dolce_ALL/dacqua-dolce && python3 scripts/media/pt54f4_manager.py
```

Open `http://127.0.0.1:18174/` in the same Mac's browser. Stop the server with **Control-C** in the launching Terminal. No npm development server is required for the Manager itself.

## Usage

1. Choose family, size, finish, photographed valve/rendition, role, gallery position and revision as applicable. Choose/drop an image. The app generates the standardized filename and saves the source **exclusively** to `ingest-drop/`. This step does not make the image public.
2. **Prepare selected photo(s)** invokes F2 ImageMagick derivative generation in a unique staging batch. Originals are not overwritten. Large uploads above 64 MiB must be placed manually in intake under a validated canonical name and processed using F2.
3. Select the prepared batch and review thumbnails and filenames. **Verify & preview publication plan** invokes F3 checksum, destination and Clack-model checks without publication.
4. Only after inspecting the batch, type its complete exact batch ID and check the approval box to enable **Publish to local TEST source**. That operation copies approved files into the local repository, records the source in the external `masters` library and appends the generated JSON image index. No existing photo is overwritten. The tool does not push or deploy to production.
5. Run the frontend build and review the local website before a controlled Git commit. Published image files and the modified `publishedPhotoIndex.json` will appear in Git status.

## Security and operational boundaries

- Localhost only. Host and Origin checks plus a per-run random CSRF token protect all mutating actions. Request sizes are bounded; no external JavaScript/CDN assets are used.
- Original filenames are not trusted. Names are generated exclusively from allowlisted metadata and revalidated with F1. Image bytes and dimensions are verified by ImageMagick through F2 before leaving intake.
- New intake files use exclusive creation and reject existing names; unexpected validation errors remove only the new file.
- The GUI reuses F2 and F3 checksums, collision rejection, staging constraints, version rules, publication receipt, and rollback-on-error logic. Reusing the same photo slot requires an **increased revision**; previously published masters and photos remain intact.
- The manager accepts one upload at a time; batch processing is available for multiple previously ingested photos. It does not offer destructive delete or bulk overwrite controls.
- Business logos/backgrounds and the production Operations-panel integration remain later, separate scopes. They are not accidentally treated as product tank photos.

## Testing without approved photographs

The F4 test suite uses generated solid-color PNGs in disposable temporary directories. It validates the full sequence upload -> prepare -> plan -> explicit publish and checks that missing approval cannot publish.

```sh
cd ~/Desktop/dacqua-dolce_ALL/dacqua-dolce
python3 -m unittest discover -s scripts/media/tests -p 'test_pt54f*.py' -v
node --check scripts/media/pt54f4_ui.js
```

No live photography is altered by these tests.
