# Product photography asset naming (new assets)

Use `Family_Size_Component_Variant_vNN.png` for individual photographs.

- Example: `Refine_1p5cf_Performance_Realistic_v01.png` (`1p5cf` = 1.5 cubic feet).
- Example: `Refine_2cf_Performance_Simplified_v02.png` (`2cf` = 2.0 cubic feet).
- Capitalize family, component, and variant. Keep underscores as separators.
- Use `_thumb.png` after the version for gallery thumbnails.
- Increment vNN for a new image revision; never overwrite an approved earlier version.
- Archive image masters under `design-assets/product-photography/masters/<family>/<image-stem>/<version>/`.
- Stage full-size website PNGs and thumbnails under `frontend/public/products/media/<family>/`.
- Do not treat mutable SKUs as permanent asset identities.
- PNG copies are for review / development; WebP conversion and live catalog wiring are separate approvals.
- Previously archived files keep their existing names unless explicitly migrated.
