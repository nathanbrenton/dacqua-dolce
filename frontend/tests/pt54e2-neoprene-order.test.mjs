import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { resolve, dirname } from "node:path";

const frontendRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const source = readFileSync(resolve(frontendRoot, "src/components/catalog/ProductDetailPage.tsx"), "utf8");

test("Refine and Essence display the existing neoprene control before fitting options", () => {
  const jacket = source.indexOf("{!isHarmony ? (");
  const fittings = source.indexOf("{fittingEligible ? (");
  assert.ok(jacket >= 0, "non-Harmony jacket condition must remain intact");
  assert.ok(fittings > jacket, "jacket checkbox must be before fitting selection");
  assert.ok(source.slice(jacket, fittings).includes('className="product-photo-jacket-label"'));
  assert.ok(source.slice(jacket, fittings).includes('Black Neoprene Jacket (+$100)'));
  assert.ok(source.slice(jacket, fittings).includes('onChange={(event) => setTankFinish(event.target.checked ? "neoprene" : "stainless")}'));
  assert.ok(source.slice(fittings).includes('aria-label="Fitting selection"'));
});

test("Harmony keeps its independent jacket immediately after tank size and before PureLine", () => {
  const tankSize = source.indexOf("value={harmonyTankSize}");
  const harmony = source.indexOf('{isHarmony ? (\n                  <label className="product-photo-jacket-label">');
  const pureline = source.indexOf("presentationLabels.labels.pureline_configuration_label");
  const configurator = source.indexOf("<HarmonyCartridgeConfigurator");
  assert.ok(tankSize >= 0 && harmony > tankSize && pureline > harmony && configurator > pureline,
    "Harmony jacket must appear between tank size and PureLine options");
  assert.equal(source.match(/Black Neoprene Jacket \(\+\$100\)/g)?.length, 2);
});

test("photography controls remain separate from customer quotes", () => {
  assert.ok(source.includes('valve: valveSelectable ? "clack" : null'));
  assert.ok(source.includes('finish: configurationFamily.name === "Origin" ? null : tankFinish'));
  assert.ok(source.includes('product.sku, tankFinish,'));
});
