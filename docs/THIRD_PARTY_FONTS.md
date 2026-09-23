# Third-Party Font Policy

D'Acqua Dolce web typography uses only fonts licensed under the
SIL Open Font License 1.1 (OFL-1.1).

Do not add proprietary, commercial-only, source-available-only, or
ambiguously licensed fonts to the application.

## Current web typography

### Instrument Serif

- Package: `@fontsource/instrument-serif`
- Version pinned by project: `5.3.0`
- License: SIL Open Font License 1.1
- Role: editorial/display typography

### Cormorant Garamond

- Package: `@fontsource/cormorant-garamond`
- Version pinned by project: `5.3.0`
- License: SIL Open Font License 1.1
- Role: classical editorial, culinary, and hospitality display typography

### Newsreader

- Package: `@fontsource-variable/newsreader`
- Version pinned by project: `5.3.0`
- License: SIL Open Font License 1.1
- Role: literary, editorial, and wellness-oriented display typography

### Manrope

- Package: `@fontsource-variable/manrope`
- Version pinned by project: `5.3.0`
- License: SIL Open Font License 1.1
- Role: body copy, navigation, forms, UI, and precision-oriented typography

### Inter

- Package: `@fontsource-variable/inter`
- Version pinned by project: `5.3.0`
- License: SIL Open Font License 1.1
- Role: technical, data-heavy, and neutral UI typography

### Source Sans 3

- Package: `@fontsource-variable/source-sans-3`
- Version pinned by project: `5.3.0`
- License: SIL Open Font License 1.1
- Role: humanist contemporary body, UI, and display typography

## Distribution

Webfont binaries are obtained through the pinned npm/Fontsource dependencies
and bundled into the production frontend build. The public site therefore
does not depend on fonts installed on the visitor's operating system or on a
runtime Google Fonts request.

If font files are ever copied or distributed outside their npm package
mechanism, preserve the corresponding SIL Open Font License text with the
distributed assets.

The local macOS Font Book installation is a design/development convenience
only and is not part of the production runtime.
