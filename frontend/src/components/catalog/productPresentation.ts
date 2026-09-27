import type { CatalogProduct } from "../../api/catalog";

export type ProductPresentation = {
  familyName: string;
  systemType: string | null;
  technologyLabel: string | null;
  catalogSummary: string | null;
  education: string | null;
};

const HARMONY_CLEAR_SKU = "DD15CAT-TTACPTV";

export function getProductPresentation(
  product: CatalogProduct,
): ProductPresentation {
  if (product.sku === HARMONY_CLEAR_SKU) {
    return {
      familyName: "Harmony",
      systemType: "Water Conditioner",
      technologyLabel: "Featuring CLEAR Technology",
      catalogSummary:
        "Non-backwashing whole-home water conditioning featuring CLEAR Technology, with no electrical power or backwash drain required.",
      education:
        "CLEAR restructures hardness minerals into microscopic crystalline forms so they are less likely to adhere as scale. D'Acqua Dolce describes these forms as Crystal Aggregate Matrix (CAM).",
    };
  }

  return {
    familyName: product.name,
    systemType: null,
    technologyLabel: null,
    catalogSummary: null,
    education: null,
  };
}
