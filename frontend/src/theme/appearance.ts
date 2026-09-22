export const APPEARANCE_MODES = [
  "light",
  "dark",
] as const;

export type AppearanceMode =
  (typeof APPEARANCE_MODES)[number];

export const DEFAULT_APPEARANCE:
  AppearanceMode = "dark";

export const DEFAULT_ACCOUNT_APPEARANCE:
  AppearanceMode = "light";

const OPERATIONS_APPEARANCE_STORAGE_KEY =
  "dacqua-dolce-appearance-v1";

const ACCOUNT_APPEARANCE_STORAGE_KEY =
  "dacqua-dolce-account-appearance-v1";

export function isAppearanceMode(
  value: string,
): value is AppearanceMode {
  return APPEARANCE_MODES.includes(
    value as AppearanceMode,
  );
}

function getStoredAppearance(
  storageKey: string,
  fallback: AppearanceMode,
): AppearanceMode {
  const stored = localStorage.getItem(
    storageKey,
  );

  if (
    stored !== null
    && isAppearanceMode(stored)
  ) {
    return stored;
  }

  return fallback;
}

export function getInitialAppearance():
  AppearanceMode {
  return getStoredAppearance(
    OPERATIONS_APPEARANCE_STORAGE_KEY,
    DEFAULT_APPEARANCE,
  );
}

export function saveAppearance(
  appearance: AppearanceMode,
): void {
  localStorage.setItem(
    OPERATIONS_APPEARANCE_STORAGE_KEY,
    appearance,
  );
}

export function getInitialAccountAppearance():
  AppearanceMode {
  return getStoredAppearance(
    ACCOUNT_APPEARANCE_STORAGE_KEY,
    DEFAULT_ACCOUNT_APPEARANCE,
  );
}

export function saveAccountAppearance(
  appearance: AppearanceMode,
): void {
  localStorage.setItem(
    ACCOUNT_APPEARANCE_STORAGE_KEY,
    appearance,
  );
}
