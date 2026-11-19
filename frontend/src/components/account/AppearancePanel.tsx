// Site theme and light/dark appearance choices on the account page.
// Styles: ./AccountAppearance.css

import { type AppearanceMode } from "../../theme/appearance";
import {
  DEFAULT_THEME,
  isThemeId,
  type ThemeId,
  THEMES,
} from "../../theme/themes";
import { AppearanceToggle } from "../theme/AppearanceToggle";

type AppearancePanelProps = {
  theme: ThemeId;
  onThemeChange: (theme: ThemeId) => void;
  appearance: AppearanceMode;
  onAppearanceChange: (
    appearance: AppearanceMode,
  ) => void;
};

export function AppearancePanel({
  theme,
  onThemeChange,
  appearance,
  onAppearanceChange,
}: AppearancePanelProps) {
  return (
    <section className="account-panel">
      <h2>Appearance</h2>

      <div className="account-appearance-controls">
        <label
          className="account-appearance-field"
          htmlFor="account-theme"
        >
          <span>Visual theme</span>

          <select
            id="account-theme"
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
        </label>

        <div className="account-appearance-mode">
          <div>
            <strong>Page appearance</strong>
            <p className="account-muted">
              Choose light or dark mode for
              your account workspace.
            </p>
          </div>

          <AppearanceToggle
            appearance={appearance}
            onAppearanceChange={
              onAppearanceChange
            }
          />
        </div>
      </div>
    </section>
  );
}
