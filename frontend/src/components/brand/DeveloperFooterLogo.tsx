import {
  BrandLogo,
} from "./BrandLogo";
import {
  type LogoVariantId,
} from "../../theme/branding";

type DeveloperFooterLogoProps = {
  variant: LogoVariantId;
  controlsOpen: boolean;
  onToggleControls: () => void;
};

export function DeveloperFooterLogo({
  variant,
  controlsOpen,
  onToggleControls,
}: DeveloperFooterLogoProps) {
  const developerMode =
    import.meta.env.VITE_DEVELOPER_MODE
    === "true";

  if (!developerMode) {
    return (
      <div className="footer-brand-frame">
        <BrandLogo
          variant={variant}
          filtrationSystems
          className="footer-logo"
        />
      </div>
    );
  }

  return (
    <button
      type="button"
      className="footer-logo-trigger"
      aria-label="Toggle developer visual controls"
      aria-expanded={controlsOpen}
      onClick={onToggleControls}
    >
      <span className="footer-brand-frame">
        <BrandLogo
          variant={variant}
          filtrationSystems
          className="footer-logo"
        />
      </span>
    </button>
  );
}
