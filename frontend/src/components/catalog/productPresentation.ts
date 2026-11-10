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
  promise: string | null;
  highlights: readonly string[];
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
      promise: family.promise,
      // The pass-through valve has no cartridge housings, so the Pureline
      // point is replaced rather than promised.
      highlights: isPassThrough
        ? [
          ...family.highlights.slice(0, 2),
          "This configuration has no cartridge filtration. Choose Pureline Solo, Duo or Trio to add it.",
        ]
        : family.highlights,
      catalogSummary: null,
      // Wording follows docs/PT14_CLIENT_PRODUCT_DIRECTION.md: the approved
      // CLEAR explanation and acronym, with no hardness-reduction claim.
      education: isHarmony
        ? "CLEAR is D'Acqua Dolce's water-conditioning technology. It restructures hardness minerals into microscopic crystalline forms so they are less likely to adhere as scale. This is conditioning, not softening: calcium and magnesium stay in your water."
        : null,
      technologyFacts: isHarmony ? [
        { label: "CLEAR", value: "Crystal Lattice Enabling Anti-Scale Reduction" },
        { label: "CAM", value: "Crystal Aggregate Matrix: the microscopic crystalline form associated with CLEAR conditioning" },
        { label: "CAM Induction", value: "The conditioning component inside the tank" },
      ] : [],
      technologyGuidance: isHarmony
        ? "CLEAR does not lower your water's measured hardness. What Pureline cartridges filter depends on the cartridges you select and your water."
        : null,
      installationFacts: isHarmony ? [
        { label: "Filtration", value: configuration.details },
      ] : [],
      ownershipGuidance: isHarmony
        ? (isPassThrough
          ? "This configuration has no Pureline cartridges, so it does not filter for taste, odor or compounds."
          : "Pureline cartridges are replaceable. Plan to replace them at least every six months where applicable; actual service life depends on your water, your usage and the cartridge.")
        : null,
    };
  }

  return {
    categoryName: product.identity.category,
    familyName: product.identity.family,
    variantLabel: product.identity.variant,
    systemType: product.system_type,
    technologyLabel: null,
    promise: null,
    highlights: [],
    catalogSummary: null,
    education: null,
    technologyFacts: [],
    technologyGuidance: null,
    installationFacts: [],
    ownershipGuidance: null,
  };
}
