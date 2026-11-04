# PT54-F9 — Local TEST Client Change Center

## Purpose

Provides a lightweight register for future customer feedback and requested presentation changes. Runs on `http://127.0.0.1:18175/` on the TEST Mac only; links to the existing local Media Manager (`http://127.0.0.1:18174/`). Never edits product pages, catalogs, images, captions, orders, prices, migrations, Git, or PROD as a side effect of recording or approving a request.

## Data lifecycle

- **Draft:** record client feedback and before/after wording, supporting references, notes, and acceptance criteria.
- **In review:** ready for a recorded human decision; may return to draft or be deferred/rejected.
- **Approved:** requires explicit reviewer name and exact typed confirmation `APPROVE CR-00001` (matching the actual request ID). This is **recorded review evidence only**, not an authenticated authorization or implementation.
- Approved records are locked until reopened, which clears their approval attribution.
- **Export:** writes only approved requests, with audit history and a source revision, to a timestamped JSON file under `~/Desktop/dacqua-dolce_build-assets/change-center/exports/`. SHA-256 is printed. Export is not a Git commit or a deployable release.

Records live at `~/Desktop/dacqua-dolce_build-assets/change-center/requests.json` **outside Git**; backups are made before each update. No user-input path is interpreted as a filesystem path. The local server binds to `127.0.0.1`, checks host, Origin and per-server CSRF tokens, validates request size and fields, serializes writes, and uses atomic file replacement. Do not expose the service through a reverse proxy or bind a public network interface.

## Launch

From TEST macOS Terminal:

```sh
cd ~/Desktop/dacqua-dolce && python3 scripts/change_center/pt54f9_server.py
```

Open `http://127.0.0.1:18175/` in the same machine. Ctrl-C terminates the server. The Media Manager can run alongside it in a second Terminal.

## Release workflow boundary

This milestone is the *request register*, not a complete content-management or deployment tool. Client-request approval by itself **does not prove that the requested change was implemented or tested**. Future F10/F11 work will bind approved requests to actual TEST source/asset changes and assemble a release-candidate change report; the existing exact-revision GitHub/PROD deployment procedure remains separately controlled.

For sensitive business logic (pricing, taxes, inventory, payments), capture the request here but continue using the established formal technical review before changing code.
