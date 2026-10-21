import type { CatalogProduct } from "../../api/catalog";
import { getConfiguration, getConfigurationFamily } from "./productConfigurations";

export type ProductPresentationFact = {
  label: string;
  value: string;
};

export type ProductPresentation = {
  categoryName: string;
  familyName: string;
  variantLabel: string | null;
  systemType: string | null;
  technologyLabel: string | null;
  catalogSummary: string | null;
  education: string | null;
  technologyFacts: readonly ProductPresentationFact[];
  technologyGuidance: string | null;
  installationFacts: readonly ProductPresentationFact[];
  ownershipGuidance: string | null;
};

export function getProductPresentation(product: CatalogProduct): ProductPresentation {
  const family = getConfigurationFamily(product.sku);
  const configuration = getConfiguration(product.sku);
  if (family !== null && configuration !== null) {
    const isHarmony = family.name === "Harmony";
    const isPassThrough = product.sku === "DD15CLEARPTV";
    return {
      categoryName: family.name === "Origin" ? "Point-of-Use Filtration" : "Whole-Home Water Treatment",
      familyName: family.name,
      variantLabel: configuration.label,
      systemType: product.system_type,
      technologyLabel: isHarmony ? "Featuring CLEAR Technology" : null,
      catalogSummary: null,
      education: isHarmony
        ? "CLEAR is D'Acqua Dolce's branded water-conditioning approach. It is not conventional water softening; calcium and magnesium are not removed as hardness minerals."
        : null,
      technologyFacts: isHarmony ? [
        { label: "CLEAR", value: "Crystal Lattice Enabling Anti-Scale Reduction" },
        { label: "CAM", value: "Crystal Aggregate Matrix" },
        { label: "CAM Induction", value: "Internal conditioning component" },
      ] : [],
      technologyGuidance: isHarmony
        ? "CLEAR terminology describes the conditioning approach, not a verified reduction of measured hardness. Cartridge-specific filtration performance depends on the selected media and water conditions."
        : null,
      installationFacts: isHarmony ? [
        { label: "Filtration", value: configuration.details },
      ] : [],
      ownershipGuidance: isHarmony
        ? (isPassThrough
          ? "This configuration contains no Pureline cartridge filters and should not be described as providing cartridge-based taste, odor, or compound filtration."
          : "Pureline cartridges are replaceable. Selection and replacement intervals depend on water quality, use, and cartridge specifications.")
        : null,
    };
  }

  return {
    categoryName: product.identity.category,
    familyName: product.identity.family,
    variantLabel: product.identity.variant,
    systemType: product.system_type,
    technologyLabel: null,
    catalogSummary: null,
    education: null,
    technologyFacts: [],
    technologyGuidance: null,
    installationFacts: [],
    ownershipGuidance: null,
  };
}
