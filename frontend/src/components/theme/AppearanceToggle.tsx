import {
  type AppearanceMode,
} from "../../theme/appearance";

type AppearanceToggleProps = {
  appearance: AppearanceMode;
  onAppearanceChange: (
    appearance: AppearanceMode,
  ) => void;
};

export function AppearanceToggle({
  appearance,
  onAppearanceChange,
}: AppearanceToggleProps) {
  const dark =
    appearance === "dark";

  return (
    <button
      type="button"
      className="appearance-toggle"
      aria-pressed={dark}
      aria-label={
        dark
          ? "Use light appearance"
          : "Use dark appearance"
      }
      onClick={() => {
        onAppearanceChange(
          dark ? "light" : "dark",
        );
      }}
    >
      <span>Dark mode</span>

      <span
        className="appearance-toggle-track"
        aria-hidden="true"
      >
        <span className="appearance-toggle-thumb" />
      </span>
    </button>
  );
}
