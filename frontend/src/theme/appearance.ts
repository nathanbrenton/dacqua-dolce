export const APPEARANCE_MODES = [
  "light",
  "dark",
] as const;

export type AppearanceMode =
  (typeof APPEARANCE_MODES)[number];

// The public site has historically defaulted to light. Existing
// account/operations preferences are migrated below when present.
export const DEFAULT_APPEARANCE:
  AppearanceMode = "light";

const APPEARANCE_STORAGE_KEY =
  "dacqua-dolce-appearance-v2";

const LEGACY_APPEARANCE_STORAGE_KEYS = [
  "dacqua-dolce-account-appearance-v1",
  "dacqua-dolce-appearance-v1",
] as const;

export function isAppearanceMode(
  value: string,
): value is AppearanceMode {
  return APPEARANCE_MODES.includes(
    value as AppearanceMode,
  );
}

function storedAppearance(
  storageKey: string,
): AppearanceMode | null {
  const stored = localStorage.getItem(
    storageKey,
  );

  return (
    stored !== null
    && isAppearanceMode(stored)
  )
    ? stored
    : null;
}

export function getInitialAppearance():
  AppearanceMode {
  const current = storedAppearance(
    APPEARANCE_STORAGE_KEY,
  );

  if (current !== null) {
    return current;
  }

  for (
    const legacyKey
    of LEGACY_APPEARANCE_STORAGE_KEYS
  ) {
    const legacy = storedAppearance(
      legacyKey,
    );

    if (legacy !== null) {
      localStorage.setItem(
        APPEARANCE_STORAGE_KEY,
        legacy,
      );
      return legacy;
    }
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
