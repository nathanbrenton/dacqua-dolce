export const LOGO_VARIANTS = [
  {
    id: "monochrome",
    label: "Monochrome",
    path: "/brand/logos/dacqua-dolce-logo-monochrome-transparent.webp",
    filtrationPath:
      "/brand/logos/dacqua-dolce-logo-monochrome-filtration-systems-transparent.webp",
    alt: "D'Acqua Dolce",
  },
  {
    id: "metallic-aqua",
    label: "Metallic / Aqua",
    path: "/brand/logos/dacqua-dolce-logo-metallic-aqua-transparent.webp",
    filtrationPath:
      "/brand/logos/dacqua-dolce-logo-metallic-aqua-filtration-systems-transparent.webp",
    alt: "D'Acqua Dolce",
  },
  {
    id: "monochrome-filtration",
    label: "Monochrome + Filtration Systems",
    path:
      "/brand/logos/dacqua-dolce-logo-monochrome-filtration-systems-transparent.webp",
    filtrationPath:
      "/brand/logos/dacqua-dolce-logo-monochrome-filtration-systems-transparent.webp",
    alt: "D'Acqua Dolce Filtration Systems",
  },
  {
    id: "metallic-aqua-filtration",
    label: "Metallic / Aqua + Filtration Systems",
    path:
      "/brand/logos/dacqua-dolce-logo-metallic-aqua-filtration-systems-transparent.webp",
    filtrationPath:
      "/brand/logos/dacqua-dolce-logo-metallic-aqua-filtration-systems-transparent.webp",
    alt: "D'Acqua Dolce Filtration Systems",
  },
] as const;

export type LogoVariantId =
  (typeof LOGO_VARIANTS)[number]["id"];

export const DEFAULT_LOGO_VARIANT: LogoVariantId =
  "metallic-aqua";

export function isLogoVariantId(
  value: string,
): value is LogoVariantId {
  return LOGO_VARIANTS.some(
    (logo) => logo.id === value,
  );
}

export function getLogoVariant(
  id: LogoVariantId,
) {
  return (
    LOGO_VARIANTS.find(
      (logo) => logo.id === id,
    )
    ?? LOGO_VARIANTS[0]
  );
}
