export const THEMES = [
  {
    id: "lagoon-editorial",
    label: "Lagoon Editorial",
  },
  {
    id: "quiet-mineral",
    label: "Quiet Mineral",
  },
  {
    id: "culinary-atelier",
    label: "Culinary Atelier",
  },
  {
    id: "performance-precision",
    label: "Performance Precision",
  },
  {
    id: "botanical-wellness",
    label: "Botanical Wellness",
  },
  {
    id: "coastal-stone",
    label: "Coastal Stone",
  },
] as const;

export type ThemeId = (typeof THEMES)[number]["id"];

export const DEFAULT_THEME: ThemeId = "lagoon-editorial";

export function isThemeId(value: string): value is ThemeId {
  return THEMES.some((theme) => theme.id === value);
}
