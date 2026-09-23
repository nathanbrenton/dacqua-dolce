export const TYPOGRAPHY_SCHEMES = [
  {
    id: "editorial-modern",
    label: "Editorial Modern",
    detail: "Instrument Serif + Manrope",
  },
  {
    id: "editorial-classic",
    label: "Editorial Classic",
    detail: "Cormorant Garamond + Manrope",
  },
  {
    id: "literary-wellness",
    label: "Literary Wellness",
    detail: "Newsreader + Manrope",
  },
  {
    id: "precision-sans",
    label: "Precision Sans",
    detail: "Manrope throughout",
  },
  {
    id: "technical-neutral",
    label: "Technical Neutral",
    detail: "Inter throughout",
  },
  {
    id: "humanist-contemporary",
    label: "Humanist Contemporary",
    detail: "Source Sans 3 throughout",
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
