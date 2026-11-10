import {
  HARMONY_CARTRIDGES, PURELINE_CATEGORIES, PURELINE_HOUSINGS,
  harmonyHousingCountForSku, type PurelineHousingPosition,
  type PurelineHousingChoice, type PurelineHousingSelections, type PurelineCategory,
} from "./harmonyCartridges";

type Props = {
  sku: string;
  selections: PurelineHousingSelections;
  onChange: (housing: PurelineHousingPosition, choice: PurelineHousingChoice) => void;
};

/** Each housing is a physical position. Cartridge type is chosen independently per housing. */
export function HarmonyCartridgeConfigurator({ sku, selections, onChange }: Props) {
  const count = harmonyHousingCountForSku(sku);
  if (count === 0) return null;
  return (
    <div className="product-pureline-configurator" aria-label="Pureline cartridge configuration">
      <h3 className="product-pureline-heading">Choose a cartridge for each housing</h3>
      {PURELINE_HOUSINGS.slice(0, count).map((housing, index) => {
        const choice = selections[housing] ?? { category: "", cartridge: "", otherDescription: "" };
        return (
          <div key={housing} className="product-pureline-housing">
            <p className="product-pureline-position">Housing {index + 1} — 20-inch cartridge housing</p>
            <label>
              <span>CARTRIDGE TYPE</span>
              <select value={choice.category}
                onChange={(event) => onChange(housing, {
                  category: event.target.value as PurelineCategory | "", cartridge: "", otherDescription: "",
                })}>
                <option value="">Choose a cartridge type</option>
                {PURELINE_CATEGORIES.map((category) => (
                  <option key={category} value={category}>
                    {category === "other" ? "Other — ask our team" : category[0].toUpperCase() + category.slice(1)}
                  </option>
                ))}
              </select>
            </label>
            {choice.category && choice.category !== "other" ? (
              <label>
                <span>CARTRIDGE OPTION</span>
                <select value={choice.cartridge} onChange={(event) => onChange(housing, { ...choice, cartridge: event.target.value })}>
                  <option value="">Choose an option</option>
                  {HARMONY_CARTRIDGES[choice.category].map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </label>
            ) : null}
            {choice.category === "other" ? (
              <label>
                <span>DESIRED MEDIA OR CARTRIDGE (OPTIONAL)</span>
                <input maxLength={120} type="text" value={choice.otherDescription}
                  placeholder="Tell us what you need and we'll confirm what's available"
                  onChange={(event) => onChange(housing, { ...choice, otherDescription: event.target.value })} />
              </label>
            ) : null}
          </div>
        );
      })}
      <p className="product-ownership-guidance">
        Each housing can hold a different cartridge. Your choices are sent with your quote
        request, and we confirm fit, pricing and availability with you before anything is final.
      </p>
    </div>
  );
}
