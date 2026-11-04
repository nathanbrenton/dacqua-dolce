/** PT54-G3: local, display-only Aesthetic Lab preference. */
export const BACKGROUND_LOGO_STORAGE_KEY = "dacqua-dolce-background-logo-visible-v1";
export const DEFAULT_BACKGROUND_LOGO_VISIBLE = true;

/** Private workspaces do not display the public marketing watermark. */
export function isBackgroundLogoAllowedPath(path: string): boolean {
  return !/^\/(?:operations|account)(?:\/|$)/i.test(path);
}

export function getInitialBackgroundLogoVisible(): boolean {
  try {
    const stored = localStorage.getItem(BACKGROUND_LOGO_STORAGE_KEY);
    if (stored === "true") return true;
    if (stored === "false") return false;
    // No saved preference: display the background logo by default.
    return DEFAULT_BACKGROUND_LOGO_VISIBLE;
  } catch {
    // Browser storage may be blocked; a decorative background must not break the app.
    return DEFAULT_BACKGROUND_LOGO_VISIBLE;
  }
}

export function saveBackgroundLogoVisible(visible: boolean): void {
  try {
    localStorage.setItem(BACKGROUND_LOGO_STORAGE_KEY, visible ? "true" : "false");
  } catch {
    // The toggle still works for the current page even when persistence is blocked.
  }
}
