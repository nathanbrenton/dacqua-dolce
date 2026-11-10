/** Owner-confirmed PT41 SKU catalog; no prices or equipment dimensions inferred. */
export type Configuration = {
  sku: string;
  label: string;
  details: string;
};

export type ConfigurationFamily = {
  name: string;
  defaultSku: string;
  /** Catalog-card summary. */
  summary: string;
  /** One-line promise shown under the family name on the product page. */
  promise: string;
  /** Short "at a glance" points; every point restates an approved catalog fact. */
  highlights: readonly string[];
  configurations: readonly Configuration[];
};

export const CONFIGURATION_FAMILIES: readonly ConfigurationFamily[] = [
  {
    name: "Refine",
    defaultSku: "DD15SOFT",
    summary: "Softened water for the whole home, designed to address the hardness minerals behind scale and spotting.",
    promise: "Softened water for the whole home.",
    highlights: [
      "Conventional softening with a brine tank.",
      "Two tank sizes: 1.5 and 2.0 cubic feet.",
      "Simple upkeep: check the salt about once a month.",
    ],
    configurations: [
      { sku: "DD15SOFT", label: "1.5 Cubic Feet", details: "Whole-home water softener" },
      { sku: "DD20SOFT", label: "2.0 Cubic Feet", details: "Whole-home water softener" },
    ],
  },
  {
    name: "Essence",
    defaultSku: "DD15CATRV",
    summary: "Whole-home carbon filtration to help address unwanted tastes, odors and certain compounds.",
    promise: "Whole-home carbon filtration for taste and odor.",
    highlights: [
      "Treats the water for the whole home, not a single tap.",
      "Rinses its own carbon media automatically.",
      "Two tank sizes: 1.5 and 2.0 cubic feet.",
    ],
    configurations: [
      { sku: "DD15CATRV", label: "1.5 Cubic Feet", details: "Automatic-rinse carbon filtration" },
      { sku: "DD20CATRV", label: "2.0 Cubic Feet", details: "Automatic-rinse carbon filtration" },
    ],
  },
  {
    name: "Harmony",
    defaultSku: "DD15CLEARPL2",
    summary: "Salt-free whole-home conditioning with CLEAR Technology, plus optional Pureline cartridge filtration for taste and odor.",
    promise: "Whole-home conditioning without brine-tank salt.",
    highlights: [
      "CLEAR conditions hardness minerals so they are less likely to adhere as scale.",
      "Conditioning, not softening: calcium and magnesium stay in your water.",
      "Add Pureline cartridge filtration with one, two or three housings.",
    ],
    configurations: [
      { sku: "DD15CLEARPL1", label: "Pureline Solo", details: "One configurable Pureline cartridge housing" },
      { sku: "DD15CLEARPL2", label: "Pureline Duo", details: "Two configurable Pureline cartridge housings" },
      { sku: "DD15CLEARPL3", label: "Pureline Trio", details: "Three configurable Pureline cartridge housings" },
      { sku: "DD15CLEARPTV", label: "Pass-Through Valve Only", details: "No Pureline cartridge housings" },
    ],
  },
  {
    name: "Origin",
    defaultSku: "DD6ROAE",
    summary: "Point-of-use reverse osmosis for drinking and cooking water, with an optional Alkaline Enhancer for added mineral content.",
    promise: "Reverse osmosis for the water you drink and cook with.",
    highlights: [
      "Point-of-use filtration, installed where you use the water.",
      "Choose five stages, or six with an Alkaline Enhancer remineralization cartridge.",
    ],
    configurations: [
      { sku: "DD5RO", label: "Five Stage", details: "Five-stage reverse osmosis" },
      { sku: "DD6ROAE", label: "Six Stage + Alkaline Enhancer", details: "Six-stage reverse osmosis with remineralization" },
    ],
  },
];

export function getConfigurationFamily(sku: string): ConfigurationFamily | null {
  return CONFIGURATION_FAMILIES.find((family) =>
    family.configurations.some((configuration) => configuration.sku === sku)
  ) ?? null;
}

export function getConfiguration(sku: string): Configuration | null {
  const family = getConfigurationFamily(sku);
  return family?.configurations.find((configuration) => configuration.sku === sku) ?? null;
}
