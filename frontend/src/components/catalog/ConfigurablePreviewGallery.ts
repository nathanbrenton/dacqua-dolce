import { clackConceptImageForOrderNo } from "./clackConceptImage";

/** Unapproved, LOCAL Vite-only product photography previews. */
export type ConfigurablePreviewTile = {
  id: "system" | "jacket" | "folded" | "hookup" | "brine" | "dimensions" | "filter" | "storage" | "alkaline";
  label: string;
  path: string | null;
  alt: string;
};

type ProductPreviewSet = {
  bare: string;
  jacket: string;
  size: string;
};

/** Local-only image sets; no approved catalog-image mutation. */
const PRODUCT_PREVIEW_SETS: Readonly<Record<string, ProductPreviewSet>> = {
  DD15CATRV: {
    bare: "/__dd_image_preview/essence/DD15CATRV-bare.png",
    jacket: "/__dd_image_preview/essence/DD15CATRV-jacket.png",
    size: "1.5",
  },
  DD20CATRV: {
    bare: "/__dd_image_preview/essence/DD20CATRV-bare.png",
    jacket: "/__dd_image_preview/essence/DD20CATRV-jacket.png",
    size: "2.0",
  },
  DD15SOFT: {
    bare: "/__dd_image_preview/refine/DD15SOFT-bare.png",
    jacket: "/__dd_image_preview/refine/DD15SOFT-jacket.png",
    size: "1.5",
  },
  DD20SOFT: {
    bare: "/__dd_image_preview/refine/DD20SOFT-bare.png",
    jacket: "/__dd_image_preview/refine/DD20SOFT-jacket.png",
    size: "2.0",
  },
};

/** Deliberately no fabric-size claim: this is a shared accessory appearance reference. */
const FOLDED_JACKET_CONCEPT = "/__dd_image_preview/shared/neoprene-jacket-15-folded.png";

export function getConfigurablePreviewGallery(
  sku: string,
  selectedFittingOrderNo: string | null,
): ConfigurablePreviewTile[] {
  // Origin uses a variant-specific RO assembly, not a Clack connection fitting.
  // The supplied measurement references have arrows but no verified numbers.
  if (sku === "DD5RO" || sku === "DD6ROAE") {
    const prefix = "/__dd_image_preview/origin/";
    const alkaline = sku === "DD6ROAE";
    const variant = alkaline ? "Alkaline Plus · six-stage" : "Standard · five-stage";
    return [
      { id: "dimensions", label: "Measurement view", path: `${prefix}${sku}-dimensions.png`,
        alt: `Unapproved ${variant} system layout with dimension arrows only, no numeric sizes` },
      { id: "system", label: `Complete system · ${variant}`, path: `${prefix}${sku}-hero.png`,
        alt: `Unapproved AI rendering of Origin ${variant} and pressure storage tank, no measurement arrows` },
      { id: "filter", label: "Filter assembly", path: `${prefix}${sku}-filter.png`,
        alt: `Unapproved AI concept of Origin ${variant} filter cartridge assembly without storage tank` },
      { id: "storage", label: "Storage tank", path: `${prefix}storage-tank.png`,
        alt: "Unapproved AI concept of separate Origin reverse-osmosis pressure storage tank" },
      ...(alkaline ? [{ id: "alkaline" as const, label: "Alkaline stage detail",
        path: `${prefix}DD6ROAE-alkaline-detail.png`,
        alt: "Unapproved close-up AI concept of the added Origin Alkaline Plus inline stage" }] : []),
    ];
  }
  const product = PRODUCT_PREVIEW_SETS[sku];
  if (product === undefined) return [];
  const suffix = `${product.size} cf`;
  const fittingPath = clackConceptImageForOrderNo(selectedFittingOrderNo);
  if (sku === "DD15SOFT" || sku === "DD20SOFT") {
    const prefix = "/__dd_image_preview/refine/";
    return [
      { id: "dimensions", label: `Measurements · ${suffix}`,
        path: `${prefix}${sku}-dimensions.png`,
        alt: `Owner-supplied Refine ${suffix} system dimension diagram showing both stainless softener tank and brine tank` },
      { id: "system", label: `Complete system · ${suffix}`, path: product.bare,
        alt: `Unapproved AI concept of Refine ${suffix} stainless softener and black brine tank, without measurements` },
      { id: "jacket", label: `Jacket fitted · ${suffix}`, path: product.jacket,
        alt: `Unapproved AI concept of Refine ${suffix} with a fitted black neoprene sleeve on the softener tank and separate brine tank` },
      { id: "brine", label: "Brine tank", path: `${prefix}brine-tank.png`,
        alt: "Unapproved AI studio concept of the separate black Refine brine tank" },
      { id: "folded", label: `Folded jacket · ${suffix}`,
        path: sku === "DD15SOFT" ? FOLDED_JACKET_CONCEPT : `${prefix}neoprene-jacket-20-folded.png`,
        alt: `Black neoprene jacket accessory concept for ${suffix}; dimensions and sizing to verify` },
      { id: "hookup", label: "Selected hookup", path: fittingPath,
        alt: selectedFittingOrderNo === null
          ? "Select a hookup size and fitting type to preview hardware"
          : `Unapproved AI concept of Clack connection fitting ${selectedFittingOrderNo}` },
    ];
  }
  return [
    { id: "system", label: `Stainless tank · ${suffix}`, path: product.bare,
      alt: `Unapproved image concept showing bare stainless Essence tank, ${suffix}` },
    { id: "jacket", label: `Jacket fitted · ${suffix}`, path: product.jacket,
      alt: `Unapproved image concept showing Essence ${suffix} tank wearing neoprene jacket` },
    { id: "folded", label: "Folded neoprene jacket", path: FOLDED_JACKET_CONCEPT,
      alt: "Representative folded black neoprene jacket concept; actual size varies with tank" },
    { id: "hookup", label: "Selected hookup", path: fittingPath,
      alt: selectedFittingOrderNo === null
        ? "Select a hookup size and type to preview hardware"
        : `Unapproved AI illustration of Clack connection fitting ${selectedFittingOrderNo}` },
  ];
}
