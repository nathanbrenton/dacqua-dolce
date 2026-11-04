import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const source = readFileSync(new URL('../src/components/catalog/ProductDetailPage.tsx', import.meta.url), 'utf8');
const label = 'Black Neoprene Jacket (+$100)';

test('PT54-G2.2: Harmony neoprene checkbox follows tank size and precedes PureLine', () => {
  const size = source.indexOf('value={harmonyTankSize}');
  const jacket = source.indexOf('{isHarmony ? (\n                  <label className="product-photo-jacket-label">');
  const pureline = source.indexOf('presentationLabels.labels.pureline_configuration_label');
  const cartridge = source.indexOf('<HarmonyCartridgeConfigurator');
  const notice = source.indexOf('<PureLineMaintenanceNotice />');
  const clear = source.indexOf('aria-label="About CLEAR Technology"');
  assert.ok(size >= 0 && jacket > size && pureline > jacket && cartridge > pureline && notice > cartridge && clear > notice);
  assert.equal(source.split('{isHarmony ? (\n                  <label className="product-photo-jacket-label">').length - 1, 1,
    'Harmony jacket checkbox should occur once');
  assert.equal(source.split('Control valve: Pass-Through Valve with red caps.').length - 1, 1,
    'Harmony technical note should occur once');
  const jacketBlock = source.slice(jacket, source.indexOf(') : null}', jacket) + ') : null}'.length);
  assert.match(jacketBlock, /checked=\{tankFinish === "neoprene"\}/);
  assert.match(jacketBlock, /setTankFinish\(event\.target\.checked \? "neoprene" : "stainless"\)/);
  assert.ok(jacketBlock.includes(label));
});

test('PT54-G2.2: keep the independent Refine/Essence jacket control and other layout', () => {
  assert.equal(source.split(label).length - 1, 2, 'one shared non-Harmony control and one Harmony control');
  const other = source.indexOf('{!isHarmony ? (');
  const size = source.indexOf('value={harmonyTankSize}');
  const harmony = source.indexOf('{isHarmony ? (\n                  <label className="product-photo-jacket-label">');
  const fitting = source.indexOf('{fittingEligible ? (');
  assert.ok(other > size && other > harmony && fitting > other, 'non-Harmony jacket still precedes fittings');
  const section = source.indexOf('{presentation.installationFacts.length > 0 ? (');
  const clear = source.indexOf('aria-label="About CLEAR Technology"');
  assert.ok(clear >= 0 && section > clear, 'G2.1 CLEAR placement remains intact');
  assert.equal((source.match(/<ProductImageNotice \/>/g) ?? []).length, 1);
  assert.equal((source.match(/<PureLineMaintenanceNotice \/>/g) ?? []).length, 1);
});
