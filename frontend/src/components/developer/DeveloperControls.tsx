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

type DeveloperControlsProps = {
  open: boolean;
  theme: ThemeId;
  onThemeChange: (theme: ThemeId) => void;
  logoVariant: LogoVariantId;
  onLogoVariantChange: (
    logo: LogoVariantId,
  ) => void;
};

export function DeveloperControls({
  open,
  theme,
  onThemeChange,
  logoVariant,
  onLogoVariantChange,
}: DeveloperControlsProps) {
  if (!open) {
    return null;
  }

  const developerMode =
    import.meta.env.VITE_DEVELOPER_MODE
    === "true";

  return (
    <aside
      className="developer-controls"
      aria-label="Appearance controls"
    >
      <span className="developer-mode-label">
        {developerMode
          ? "Developer Mode"
          : "Appearance"}
      </span>

      <label htmlFor="developer-theme">
        Visual theme
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

      {developerMode ? (
        <>
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
        </>
      ) : null}
    </aside>
  );
}
