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
  return (
    <button
      type="button"
      className="footer-logo-trigger"
      aria-label="Toggle appearance controls"
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
