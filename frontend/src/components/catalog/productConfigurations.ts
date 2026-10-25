/** Owner-confirmed PT41 SKU catalog; no prices or equipment dimensions inferred. */
export type Configuration = {
  sku: string;
  label: string;
  details: string;
};

export type ConfigurationFamily = {
  name: string;
  defaultSku: string;
  summary: string;
  configurations: readonly Configuration[];
};

export const CONFIGURATION_FAMILIES: readonly ConfigurationFamily[] = [
  {
    name: "Refine",
    defaultSku: "DD15SOFT",
    summary: "Whole-home water softening designed to address hard-water minerals, spotting and scale buildup.",
    configurations: [
      { sku: "DD15SOFT", label: "1.5 Cubic Feet", details: "Whole-home water softener" },
      { sku: "DD20SOFT", label: "2.0 Cubic Feet", details: "Whole-home water softener" },
    ],
  },
  {
    name: "Essence",
    defaultSku: "DD15CATRV",
    summary: "Whole-home carbon filtration to help address unwanted tastes, odors and applicable compounds.",
    configurations: [
      { sku: "DD15CATRV", label: "1.5 Cubic Feet", details: "Automatic-rinse carbon filtration" },
      { sku: "DD20CATRV", label: "2.0 Cubic Feet", details: "Automatic-rinse carbon filtration" },
    ],
  },
  {
    name: "Harmony",
    defaultSku: "DD15CLEARPL2",
    summary: "Whole-home CLEAR water conditioning with Pureline options for taste, odor and applicable compounds.",
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
    summary: "Six stage point-of-use drinking water system includes an optional Alkaline Enhancer for increased mineral content.",
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
