import {
  DEFAULT_THEME,
  isThemeId,
  THEMES,
  type ThemeId,
} from "../../theme/themes";

type ThemeSelectorProps = {
  theme: ThemeId;
  onThemeChange: (theme: ThemeId) => void;
};

export function ThemeSelector({
  theme,
  onThemeChange,
}: ThemeSelectorProps) {
  if (import.meta.env.VITE_DEVELOPER_MODE !== "true") {
    return null;
  }

  return (
    <aside
      className="developer-theme-selector"
      aria-label="Developer theme controls"
    >
      <span className="developer-mode-label">
        Developer Mode
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
    </aside>
  );
}
