import type { CatalogProduct } from "../../api/catalog";

export type ProductPresentationFact = {
  label: string;
  value: string;
};

export type ProductPresentation = {
  familyName: string;
  systemType: string | null;
  technologyLabel: string | null;
  catalogSummary: string | null;
  education: string | null;
  technologyFacts: readonly ProductPresentationFact[];
  technologyGuidance: string | null;
  installationFacts: readonly ProductPresentationFact[];
  ownershipGuidance: string | null;
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
        "CLEAR is D'Acqua Dolce's branded terminology for its anti-scale water-conditioning approach. Manufacturer performance statements are presented separately only when an approved source is recorded.",
      technologyFacts: [
        {
          label: "CLEAR",
          value: "Crystal Lattice Enabling Anti-Scale Reduction",
        },
        {
          label: "CAM",
          value: "Crystal Aggregate Matrix",
        },
        {
          label: "CAM Induction",
          value: "Internal conditioning component",
        },
      ],
      technologyGuidance:
        "The CLEAR name describes D'Acqua Dolce's anti-scale conditioning approach. Calcium and magnesium remain in the treated water; the terminology does not claim conventional hardness removal or a reduction in measured hardness concentration. CAM Induction is the public name for the internal conditioning component associated with CLEAR; its name does not by itself establish a physical mechanism.",
      installationFacts: [
        {
          label: "Operation",
          value: "Non-backwashing",
        },
        {
          label: "Electrical power",
          value: "Not required",
        },
        {
          label: "Backwash drain",
          value: "Not required",
        },
        {
          label: "Recommended pairing",
          value: "Duo cartridge filtration",
        },
      ],
      ownershipGuidance:
        "Harmony may be purchased individually. The preferred filtration configuration pairs it with a Duo cartridge system containing replaceable sediment and carbon filters. Replace cartridges every six months where applicable, with actual life affected by water quality, use, and system conditions; follow a pressure/clog gauge when equipped.",
    };
  }

  return {
    familyName: product.product_family ?? product.name,
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
