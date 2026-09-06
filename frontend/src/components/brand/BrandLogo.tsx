import {
  getLogoVariant,
  type LogoVariantId,
} from "../../theme/branding";

type BrandLogoProps = {
  variant: LogoVariantId;
  filtrationSystems?: boolean;
  className?: string;
};

export function BrandLogo({
  variant,
  filtrationSystems = false,
  className,
}: BrandLogoProps) {
  const logo = getLogoVariant(variant);

  return (
    <img
      className={className}
      src={
        filtrationSystems
          ? logo.filtrationPath
          : logo.path
      }
      alt={
        filtrationSystems
          ? "D'Acqua Dolce Filtration Systems"
          : logo.alt
      }
      decoding="async"
    />
  );
}
