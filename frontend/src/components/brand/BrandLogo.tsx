import {
  getLogoVariant,
  type LogoVariantId,
} from "../../theme/branding";

type BrandLogoProps = {
  variant: LogoVariantId;
  className?: string;
};

/**
 * The selected logo artwork. Header, footer and Operations all pass the same
 * variant, so the logo matches everywhere.
 */
export function BrandLogo({
  variant,
  className,
}: BrandLogoProps) {
  const logo = getLogoVariant(variant);

  return (
    <img
      className={className}
      data-logo-variant={variant}
      src={logo.path}
      alt={logo.alt}
      decoding="async"
    />
  );
}
