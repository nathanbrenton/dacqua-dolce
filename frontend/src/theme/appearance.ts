export const APPEARANCE_MODES = [
  "light",
  "dark",
] as const;

export type AppearanceMode =
  (typeof APPEARANCE_MODES)[number];

export const DEFAULT_APPEARANCE:
  AppearanceMode = "light";

const APPEARANCE_STORAGE_KEY =
  "dacqua-dolce-appearance-v1";

export function isAppearanceMode(
  value: string,
): value is AppearanceMode {
  return APPEARANCE_MODES.includes(
    value as AppearanceMode,
  );
}

export function getInitialAppearance():
  AppearanceMode {
  const stored = localStorage.getItem(
    APPEARANCE_STORAGE_KEY,
  );

  if (
    stored !== null
    && isAppearanceMode(stored)
  ) {
    return stored;
  }

  return DEFAULT_APPEARANCE;
}

export function saveAppearance(
  appearance: AppearanceMode,
): void {
  localStorage.setItem(
    APPEARANCE_STORAGE_KEY,
    appearance,
  );
}
