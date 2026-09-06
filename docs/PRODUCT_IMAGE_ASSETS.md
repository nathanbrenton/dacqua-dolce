# D'Acqua Dolce Product Image Asset Manifest

Source: four ZIP archives supplied by the project owner on 2026-09-05.

## Processing policy

- No stylistic edits.
- No recoloring.
- No object removal or addition.
- No crop or composition change.
- Aspect ratio preserved.
- Downscaled only when the source exceeded the web target size.
- Lossy web compression only for delivery efficiency.
- Each unique source image has a WebP primary and progressive JPEG fallback.
- Source SHA-256 hashes are retained in `manifest.json`.

## Deduplication

The four ZIPs contained 21 image entries but only 17 unique image files.
`skudims 1.zip` duplicated four files already present in `skudims.zip`:

- `DD15CATPTV.jpg`
- `DD15CATRV.jpg`
- `DD5RO.jpg`
- `DD5ROAE.jpg`

The duplicate copies were not emitted twice.

## Unique web assets

### `1-5cf-pass-through-valve-dimensions`

- Source ZIP: `dims 1.zip`
- Source filename: `OneFiveWithoutKlack.jpg`
- Source dimensions: 3210×6419
- Web dimensions: 1400×2800
- Source SHA-256: `a27733ce1fd741115f05e73e9aa3d21314b906f60a98c0e1c43eaf152c3dd273`
- WebP: `/products/media/1-5cf-pass-through-valve-dimensions.webp`
- JPEG: `/products/media/1-5cf-pass-through-valve-dimensions.jpg`

### `1-5cf-pass-through-with-prefilter-dimensions`

- Source ZIP: `dims 1.zip`
- Source filename: `OneFiveWithFilterWithoutKlack.jpg`
- Source dimensions: 3210×6419
- Web dimensions: 1400×2800
- Source SHA-256: `47b264fcf43563c64c0f1c6234be6723102e02165ea4ae08495909f211be65f6`
- WebP: `/products/media/1-5cf-pass-through-with-prefilter-dimensions.webp`
- JPEG: `/products/media/1-5cf-pass-through-with-prefilter-dimensions.jpg`

### `1-5cf-regenerating-valve-dimensions`

- Source ZIP: `dims 1.zip`
- Source filename: `OneFiveWithKlack.jpg`
- Source dimensions: 3100×6199
- Web dimensions: 1400×2800
- Source SHA-256: `e23d29fa12e3a074902666ebb33757eee1678d221eb07b392d24c3098a7b719f`
- WebP: `/products/media/1-5cf-regenerating-valve-dimensions.webp`
- JPEG: `/products/media/1-5cf-regenerating-valve-dimensions.jpg`

### `1-5cf-regenerating-with-prefilter-dimensions`

- Source ZIP: `dims 1.zip`
- Source filename: `OneFiveKlackwFilter.jpg`
- Source dimensions: 3149×6299
- Web dimensions: 1400×2800
- Source SHA-256: `4ff0861b7b8c93d9e2195f64d5ce1be63878b8991e874a2cb79420b3d6673f26`
- WebP: `/products/media/1-5cf-regenerating-with-prefilter-dimensions.webp`
- JPEG: `/products/media/1-5cf-regenerating-with-prefilter-dimensions.jpg`

### `1-5cf-regenerating-with-salt-tank-dimensions`

- Source ZIP: `dims 1.zip`
- Source filename: `OneFiveWithKlackSaltTank.jpg`
- Source dimensions: 3870×6773
- Web dimensions: 1400×2450
- Source SHA-256: `418e6661961092123ded45306d489f8e9b8b0da6c1cc2a9e5d94e9fa27d9ddf2`
- WebP: `/products/media/1-5cf-regenerating-with-salt-tank-dimensions.webp`
- JPEG: `/products/media/1-5cf-regenerating-with-salt-tank-dimensions.jpg`

### `2cf-pass-through-valve-dimensions`

- Source ZIP: `dims.zip`
- Source filename: `2CubicFootWithoutKlack.jpg`
- Source dimensions: 3100×6199
- Web dimensions: 1400×2800
- Source SHA-256: `6d4cdae4a550b1b701679c2ef12b284a70bf097ef3583dece0dfeeffd19831f3`
- WebP: `/products/media/2cf-pass-through-valve-dimensions.webp`
- JPEG: `/products/media/2cf-pass-through-valve-dimensions.jpg`

### `2cf-pass-through-with-prefilter-dimensions`

- Source ZIP: `dims.zip`
- Source filename: `2cubicFootFilterWithoutValve.jpg`
- Source dimensions: 3312×6624
- Web dimensions: 1400×2800
- Source SHA-256: `373226d86f04d7f5c476006bda0b975f088657e0f3f31b7a0549019b52683abd`
- WebP: `/products/media/2cf-pass-through-with-prefilter-dimensions.webp`
- JPEG: `/products/media/2cf-pass-through-with-prefilter-dimensions.jpg`

### `2cf-regenerating-valve-dimensions`

- Source ZIP: `dims.zip`
- Source filename: `2CubicFootWithKlack.jpg`
- Source dimensions: 3100×6199
- Web dimensions: 1400×2800
- Source SHA-256: `cd5f740ce744fc26a81ff03b2d7512cfc25c9a8b3c153a78d45d305b836c8376`
- WebP: `/products/media/2cf-regenerating-valve-dimensions.webp`
- JPEG: `/products/media/2cf-regenerating-valve-dimensions.jpg`

### `2cf-regenerating-with-prefilter-dimensions`

- Source ZIP: `dims.zip`
- Source filename: `2cubicFTWithFILTERAndKlack.jpg`
- Source dimensions: 3383×6766
- Web dimensions: 1400×2800
- Source SHA-256: `2de016fcba8d68da6481903a0b43545bb13bf0f0887fb52d2ffdee772ec67a1a`
- WebP: `/products/media/2cf-regenerating-with-prefilter-dimensions.webp`
- JPEG: `/products/media/2cf-regenerating-with-prefilter-dimensions.jpg`

### `dd15cat-ttacptv-spec-dimensions`

- Source ZIP: `skudims.zip`
- Source filename: `DD15CAT-TTACPTV.jpg`
- Source dimensions: 7500×6419
- Web dimensions: 1800×1541
- Source SHA-256: `98f6e27360458aeec43a23e8798e2d2406202b702b443c07d0b0a817baa96d7b`
- WebP: `/products/media/dd15cat-ttacptv-spec-dimensions.webp`
- JPEG: `/products/media/dd15cat-ttacptv-spec-dimensions.jpg`

### `dd15cat-ttacrv-spec-dimensions`

- Source ZIP: `skudims.zip`
- Source filename: `DD15CAT-TTACRV.jpg`
- Source dimensions: 7500×6419
- Web dimensions: 1800×1541
- Source SHA-256: `6e42ea231c59c86d047a4345418698fe4044141030b22ddbd0242d7e9b32a751`
- WebP: `/products/media/dd15cat-ttacrv-spec-dimensions.webp`
- JPEG: `/products/media/dd15cat-ttacrv-spec-dimensions.jpg`

### `dd15catptv-spec-dimensions`

- Source ZIP: `skudims.zip`
- Source filename: `DD15CATPTV.jpg`
- Source dimensions: 7500×6419
- Web dimensions: 1800×1541
- Source SHA-256: `16896c3eea43bcc2f6fc071c604b67c5017fe430d40725492c0b8bb50d8dfeca`
- WebP: `/products/media/dd15catptv-spec-dimensions.webp`
- JPEG: `/products/media/dd15catptv-spec-dimensions.jpg`

### `dd15catrv-spec-dimensions`

- Source ZIP: `skudims.zip`
- Source filename: `DD15CATRV.jpg`
- Source dimensions: 7500×6419
- Web dimensions: 1800×1541
- Source SHA-256: `75259b94f09bfa34cd3b530a49afd6564ab35fe733073a3c02a15badfcabd3e8`
- WebP: `/products/media/dd15catrv-spec-dimensions.webp`
- JPEG: `/products/media/dd15catrv-spec-dimensions.jpg`

### `dd5ro-spec-dimensions`

- Source ZIP: `skudims.zip`
- Source filename: `DD5RO.jpg`
- Source dimensions: 7500×6419
- Web dimensions: 1800×1541
- Source SHA-256: `73a20f36558bd1668e9d7db07a63272937179c5f2f0698bdc20910baaddb021a`
- WebP: `/products/media/dd5ro-spec-dimensions.webp`
- JPEG: `/products/media/dd5ro-spec-dimensions.jpg`

### `dd5roae-spec-dimensions`

- Source ZIP: `skudims.zip`
- Source filename: `DD5ROAE.jpg`
- Source dimensions: 7500×6419
- Web dimensions: 1800×1541
- Source SHA-256: `898ddfa751d8c4b25a2a844bf95a409325dada4afdcdc7052fa14b6b38caacf9`
- WebP: `/products/media/dd5roae-spec-dimensions.webp`
- JPEG: `/products/media/dd5roae-spec-dimensions.jpg`

### `reverse-osmosis-with-remineralizer-dimensions`

- Source ZIP: `dims.zip`
- Source filename: `HomePage2WithReminerilaizerDIMS.jpg`
- Source dimensions: 6907×4605
- Web dimensions: 1800×1200
- Source SHA-256: `3a1fd56fca990be4210a9cd0bff457711be330ba5a9bfb593d0e0e752c5f78ce`
- WebP: `/products/media/reverse-osmosis-with-remineralizer-dimensions.webp`
- JPEG: `/products/media/reverse-osmosis-with-remineralizer-dimensions.jpg`

### `reverse-osmosis-without-remineralizer-dimensions`

- Source ZIP: `dims 1.zip`
- Source filename: `ROwithoutRemineralizerDIMS.jpg`
- Source dimensions: 6907×4605
- Web dimensions: 1800×1200
- Source SHA-256: `edbd8f18fe2d61aeeb84024532b3e08e2300802a9cad9da7cf4d1e937777f9b3`
- WebP: `/products/media/reverse-osmosis-without-remineralizer-dimensions.webp`
- JPEG: `/products/media/reverse-osmosis-without-remineralizer-dimensions.jpg`
