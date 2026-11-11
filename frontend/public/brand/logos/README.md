# D'Acqua Dolce logo web assets

Source: `DAcqua-Dolce-Logos.pdf`, page 1, supplied by the project owner.

Source PDF SHA-256:

    621af196310fcead46865367adb2f186dc2cc94e93b3a5cdf325f53f0d5ce653

Preparation policy:

- Rendered directly from the supplied PDF at 600 DPI.
- Cropped only to isolate the four supplied logo variants.
- No recoloring.
- No redrawing.
- No sharpening.
- No added effects.
- No stylistic changes.
- PNG preserves the crop as rendered from the source PDF.
- WebP is lossless and uses the same crop dimensions.

Assets:

- `dacqua-dolce-logo-monochrome.png`
- `dacqua-dolce-logo-monochrome.webp`
- `dacqua-dolce-logo-metallic-aqua.png`
- `dacqua-dolce-logo-metallic-aqua.webp`
- `dacqua-dolce-logo-monochrome-filtration-systems.png`
- `dacqua-dolce-logo-monochrome-filtration-systems.webp`
- `dacqua-dolce-logo-metallic-aqua-filtration-systems.png`
- `dacqua-dolce-logo-metallic-aqua-filtration-systems.webp`

The logos are intentionally not automatically recolored or theme-filtered.
The current application can select among the supplied source variants without
altering the artwork. The footer-logo Appearance control exposes visual-theme
selection in production, while the logo-artwork selector remains developer-mode
only.

## Transparent logo set (2026-11-10)

The customer header and footer now use transparent artwork so the logo sits
directly on the page with no white plate behind it.

Source: `DAcqua_Dolce_4_Logos_1920x1080_Transparent_PNG/`, supplied by the
project owner. Source PNG SHA-256:

    a3d921bd3248b3dcb16af5c07243e75d1cdce363b5e5447a919d5a8793e2ac43  DAcqua_Dolce_Standard_Metallic_1920x1080.png
    64d24832285e1d278a20931f841835f2b23ae0d08008f49da1883ccaa6dd32ad  DAcqua_Dolce_Standard_Silhouette_1920x1080.png
    1c331afd8726963c65952c7909a61bce99ff154d119033b7c673d0837de0e2c5  DAcqua_Dolce_Filtration_Systems_Metallic_1920x1080.png
    5698cd1c51d9231d614c45382ede5ae2197440fa6611d5481e992e88dd1a7ea3  DAcqua_Dolce_Filtration_Systems_Silhouette_1920x1080.png

Preparation:

- Trimmed to the artwork, with a 12px transparent margin, then resized to 960px wide.
- No recoloring, redrawing, sharpening, or added effects.
- PNG keeps full alpha. WebP is quality 92 with lossless alpha and is what the site serves.
- GIF was not used: it supports only on/off transparency, which leaves a jagged
  fringe around the metallic oval on any background other than the one it was cut for.

Assets (`.png` and `.webp` each):

- `dacqua-dolce-logo-metallic-aqua-transparent`
- `dacqua-dolce-logo-monochrome-transparent`
- `dacqua-dolce-logo-metallic-aqua-filtration-systems-transparent`
- `dacqua-dolce-logo-monochrome-filtration-systems-transparent`

In dark appearance the black-line (monochrome) logo is inverted with CSS so it
stays visible, the same treatment the background watermark already uses. The
metallic logo is never filtered. Operations keeps its white logo plate.
