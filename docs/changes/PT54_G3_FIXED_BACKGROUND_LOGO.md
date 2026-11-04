# PT54-G3 — Fixed Background Logo / TEST only

## Scope

- Uses the **original black oval vector logo** from the supplied D’Acqua Dolce source PDF; no PNG tracing and no additional bitmap assets.
- Decorative, stationary logo behind customer-facing content on home, product, support, legal, and general public pages.
- Excluded from `'/operations'`, `'/account'`, and descendants. A preference saved while viewing a public page cannot override those exclusions.
- Existing footer-logo Aesthetic Lab includes **Background logo visible** checkbox. Defaults off.
- Preference persists locally under `dacqua-dolce-background-logo-visible-v1`; no API writes or authenticated account setting changes.
- Same SVG scales responsively using CSS for desktop, portrait and landscape handheld viewports.
- The SVG remains original black artwork; in dark appearance CSS inverts the display to retain contrast.
- No changes to photo galleries, product selection, checkout, account pages, or operations.

## TEST visual acceptance

1. Use footer logo to open Aesthetic Lab on the home page; toggle the checkbox on, verify the logo is subtle and behind content.
2. Scroll long pages; the logo should stay fixed relative to the viewport. Verify hero, recommendation, and photo gallery interaction.
3. Navigate home → Harmony/Refine/Essence/Origin → support → privacy/terms and confirm visibility persists.
4. Visit Operations and Account; background logo must be absent even while the checkbox preference remains on.
5. Test light and dark appearances; resize to mobile portrait and landscape. Confirm logo remains inside viewport and text remains readable.
6. Refresh browser: preference persists locally; toggle off to restore the previous look.

No PROD deployment, Git push, commit, database changes or image-file cleanup.
