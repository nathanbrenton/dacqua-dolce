export const TYPOGRAPHY_SCHEMES = [
  {
    id: "editorial-modern",
    label: "Editorial Modern",
    detail: "Instrument Serif display · Manrope body · Source Sans 3 UI",
  },
  {
    id: "editorial-classic",
    label: "Editorial Classic",
    detail: "Cormorant display · Newsreader body · Manrope UI",
  },
  {
    id: "literary-wellness",
    label: "Literary Wellness",
    detail: "Newsreader display · Source Sans 3 body/UI · softer labels",
  },
  {
    id: "precision-sans",
    label: "Precision Sans",
    detail: "Manrope display/body · Inter UI/data · performance labels",
  },
  {
    id: "technical-neutral",
    label: "Technical Neutral",
    detail: "Inter display/UI · Source Sans 3 body · technical labels",
  },
  {
    id: "humanist-contemporary",
    label: "Humanist Contemporary",
    detail: "Source Sans 3 throughout · shared responsive scale",
  },
] as const;

export type TypographySchemeId =
  (typeof TYPOGRAPHY_SCHEMES)[number]["id"];

export const DEFAULT_TYPOGRAPHY_SCHEME:
  TypographySchemeId = "editorial-modern";

const TYPOGRAPHY_STORAGE_KEY =
  "dacqua-dolce-typography-v1";

export function isTypographySchemeId(
  value: string,
): value is TypographySchemeId {
  return TYPOGRAPHY_SCHEMES.some(
    (scheme) => scheme.id === value,
  );
}

export function getInitialTypography():
  TypographySchemeId {
  const stored = localStorage.getItem(
    TYPOGRAPHY_STORAGE_KEY,
  );

  if (
    stored !== null
    && isTypographySchemeId(stored)
  ) {
    return stored;
  }

  return DEFAULT_TYPOGRAPHY_SCHEME;
}

export function saveTypography(
  typography: TypographySchemeId,
): void {
  localStorage.setItem(
    TYPOGRAPHY_STORAGE_KEY,
    typography,
  );
}
