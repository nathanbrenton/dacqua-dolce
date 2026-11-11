# PT54-F10 — Local TEST Presentation Settings Editor

This is the first structured, source-controlled presentation edit surface in the Client Change Center (`http://127.0.0.1:18175/`). It is separate from the F9 request register and F6 caption editor.

## Change boundary

- **Allowed:** nine low-risk labels/headings in the product detail UI, controlled by a strict allowlist and 80-character plain-text validation.
- **Excluded:** price amounts, neoprene surcharge, stock quantities, valve commerce, warranty/legal copy, product identifiers, tax, checkout, purchasing, marketing claims, and product specifications.
- No requests are automatically approved, no Git staging/commit/push is performed, and no production data is changed.
- Change Center binds only to `127.0.0.1`, enforces same-origin and CSRF for edits, and rejects stale revisions.

## Where settings live

`frontend/src/components/catalog/presentationLabels.json` is the source-controlled TEST presentation document. Editing increments `revision`. The frontend imports it at build time, so changes can be previewed in TEST and are included only in a later reviewed Git commit / production deployment.

The local editor backs up the prior JSON at `~/Desktop/dacqua-dolce_ALL/dacqua-dolce_build-assets/change-center/presentation-backups/`. These backups do not enter the production release. Git diffs are the release-review record.

The editor uses the same HTTP port as F9, **18175**. Restart the Change Center Python server after installing F10. Refresh the TEST storefront to see saved labels. The Media Manager remains on port 18174.

## Change approval

A successful Save to TEST is an implementation event, not client approval or permission to deploy. Record an F9 change request and obtain review/acceptance separately. F11 will connect approved requests to tested source changes and produce release-candidate evidence.

## Reset

To restore a wording field, manually set its value back to the original text in the editor; do not revert unrelated uncommitted source files. Prior JSON versions are in `presentation-backups` and Git revision history after commit.
