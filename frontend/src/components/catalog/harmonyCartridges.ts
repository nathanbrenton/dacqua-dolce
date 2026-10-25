/** PT53 owner-supplied descriptive choices only; NOT orderable SKUs, pricing, or certified compatibility. */
export type PurelinePosition = "sediment" | "iron" | "carbon";
export type PurelineHousingPosition = "housing1" | "housing2" | "housing3";
export type PurelineCategory = PurelinePosition | "other";
export type PurelineHousingChoice = { category: PurelineCategory | ""; cartridge: string; otherDescription: string };
export type PurelineHousingSelections = Partial<Record<PurelineHousingPosition, PurelineHousingChoice>>;
export const PURELINE_HOUSINGS: readonly PurelineHousingPosition[] = ["housing1", "housing2", "housing3"];
export const PURELINE_CATEGORIES: readonly PurelineCategory[] = ["sediment", "carbon", "iron", "other"];
export const HARMONY_CARTRIDGES: Readonly<Record<PurelinePosition, readonly string[]>> = {
  sediment: [
    "Pleated — 30 micron",
    "Pleated polyester — 30 micron",
    "Pleated cellulose polyester — 1 micron",
    "Pleated cellulose polyester — 5 micron",
    "Pleated cellulose polyester — 20 micron",
    "Pleated cellulose polyester — 50 micron",
    "Pleated — 20 micron",
    "Sediment — 1 micron",
    "Sediment — 5 micron",
    "Sediment — 25 micron",
  ],
  carbon: [
    'GAC — 4" diameter',
    'PAC — 4" diameter (modified episolon carbon block)',
    "Non-Cellulose",
  ],
  iron: ["Iron cartridge"],
};

export function validCartridgeChoices(choices: Partial<Record<PurelinePosition, string>>): boolean {
  return (Object.entries(choices) as [PurelinePosition, string][])
    .every(([position, choice]) => !choice || HARMONY_CARTRIDGES[position]?.includes(choice));
}

/** Number of separately configurable physical Pureline housings. No SKU inference for 2.0 cf. */
export function harmonyHousingCountForSku(sku: string): number {
  switch (sku) {
    case "DD15CLEARPL1": return 1;
    case "DD15CLEARPL2": return 2;
    case "DD15CLEARPL3": return 3;
    default: return 0;
  }
}

/** Validate only known cartridge descriptions, or clearly labeled free-text inquiries. */
export function validHousingSelections(selections: PurelineHousingSelections): boolean {
  return Object.entries(selections).every(([housing, selection]) => {
    if (!PURELINE_HOUSINGS.includes(housing as PurelineHousingPosition)) return false;
    if (!selection) return false;
    const { category, cartridge, otherDescription } = selection;
    if (category === "") return !cartridge && !otherDescription;
    if (!PURELINE_CATEGORIES.includes(category)) return false;
    if (category === "other") return cartridge === "" && otherDescription.length <= 120;
    return otherDescription === "" && (!cartridge || HARMONY_CARTRIDGES[category].includes(cartridge));
  });
}
