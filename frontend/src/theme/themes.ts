export const THEMES = [
  {
    id: "baseline",
    label: "Current Baseline",
  },
  {
    id: "quiet-mineral",
    label: "Quiet Mineral",
  },
  {
    id: "lagoon-editorial",
    label: "Lagoon Editorial",
  },
  {
    id: "culinary-atelier",
    label: "Culinary Atelier",
  },
  {
    id: "performance-precision",
    label: "Performance Precision",
  },
] as const;

export type ThemeId = (typeof THEMES)[number]["id"];

export const DEFAULT_THEME: ThemeId = "lagoon-editorial";

export function isThemeId(value: string): value is ThemeId {
  return THEMES.some((theme) => theme.id === value);
}
