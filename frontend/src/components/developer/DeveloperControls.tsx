import {
  DEFAULT_APPEARANCE,
  isAppearanceMode,
  type AppearanceMode,
} from "../../theme/appearance";
import {
  DEFAULT_LOGO_VARIANT,
  isLogoVariantId,
  LOGO_VARIANTS,
  type LogoVariantId,
} from "../../theme/branding";
import {
  DEFAULT_THEME,
  isThemeId,
  THEMES,
  type ThemeId,
} from "../../theme/themes";
import {
  DEFAULT_TYPOGRAPHY_SCHEME,
  isTypographySchemeId,
  TYPOGRAPHY_SCHEMES,
  type TypographySchemeId,
} from "../../theme/typography";

type DeveloperControlsProps = {
  open: boolean;
  theme: ThemeId;
  onThemeChange: (theme: ThemeId) => void;
  appearance: AppearanceMode;
  onAppearanceChange: (
    appearance: AppearanceMode,
  ) => void;
  typography: TypographySchemeId;
  onTypographyChange: (
    typography: TypographySchemeId,
  ) => void;
  logoVariant: LogoVariantId;
  onLogoVariantChange: (
    logo: LogoVariantId,
  ) => void;
};

export function DeveloperControls({
  open,
  theme,
  onThemeChange,
  appearance,
  onAppearanceChange,
  typography,
  onTypographyChange,
  logoVariant,
  onLogoVariantChange,
}: DeveloperControlsProps) {
  if (!open) {
    return null;
  }

  return (
    <aside
      className="developer-controls"
      aria-label="Aesthetic lab"
    >
      <span className="developer-mode-label">
        Aesthetic Lab
      </span>

      <label htmlFor="developer-theme">
        Color theme
      </label>

      <select
        id="developer-theme"
        value={theme}
        onChange={(event) => {
          const value = event.target.value;

          onThemeChange(
            isThemeId(value)
              ? value
              : DEFAULT_THEME,
          );
        }}
      >
        {THEMES.map((option) => (
          <option
            key={option.id}
            value={option.id}
          >
            {option.label}
          </option>
        ))}
      </select>

      <label htmlFor="developer-appearance">
        Appearance
      </label>

      <select
        id="developer-appearance"
        value={appearance}
        onChange={(event) => {
          const value = event.target.value;

          onAppearanceChange(
            isAppearanceMode(value)
              ? value
              : DEFAULT_APPEARANCE,
          );
        }}
      >
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>

      <label htmlFor="developer-typography">
        Typography
      </label>

      <select
        id="developer-typography"
        value={typography}
        onChange={(event) => {
          const value = event.target.value;

          onTypographyChange(
            isTypographySchemeId(value)
              ? value
              : DEFAULT_TYPOGRAPHY_SCHEME,
          );
        }}
      >
        {TYPOGRAPHY_SCHEMES.map((option) => (
          <option
            key={option.id}
            value={option.id}
          >
            {option.label}
            {" — "}
            {option.detail}
          </option>
        ))}
      </select>

      <label htmlFor="developer-logo">
        Logo artwork
      </label>

      <select
        id="developer-logo"
        value={logoVariant}
        onChange={(event) => {
          const value = event.target.value;

          onLogoVariantChange(
            isLogoVariantId(value)
              ? value
              : DEFAULT_LOGO_VARIANT,
          );
        }}
      >
        {LOGO_VARIANTS.map((option) => (
          <option
            key={option.id}
            value={option.id}
          >
            {option.label}
          </option>
        ))}
      </select>
    </aside>
  );
}
