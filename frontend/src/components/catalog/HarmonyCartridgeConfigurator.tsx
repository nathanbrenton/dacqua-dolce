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
      <h3 className="product-pureline-heading">Configure each Pureline housing</h3>
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
                  placeholder="Describe what you need; we'll confirm availability"
                  onChange={(event) => onChange(housing, { ...choice, otherDescription: event.target.value })} />
              </label>
            ) : null}
          </div>
        );
      })}
      <p className="product-ownership-guidance">
        Positions can be configured independently. These are requests, not verified compatible
        assemblies or priced cartridge SKUs. Fit, performance, pricing, and availability require confirmation.
      </p>
    </div>
  );
}
