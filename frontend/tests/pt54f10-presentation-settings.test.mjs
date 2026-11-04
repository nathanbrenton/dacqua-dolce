import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
const doc = JSON.parse(readFileSync(new URL('../src/components/catalog/presentationLabels.json', import.meta.url), 'utf8'));
const page = readFileSync(new URL('../src/components/catalog/ProductDetailPage.tsx', import.meta.url), 'utf8');
const required = ['overview_heading', 'tank_size_label', 'system_configuration_label',
'fitting_size_label', 'fitting_type_label', 'connection_size_prompt',
'pureline_configuration_label', 'system_size_heading', 'media_volume_label'];
test('F10 has exact allowlisted presentation labels and product-page bindings', () => {
  assert.equal(doc.schema_version, 1);
  assert.equal(Number.isInteger(doc.revision), true);
  assert.deepEqual(Object.keys(doc.labels).sort(), [...required].sort());
  for (const key of required) {
    assert.equal(typeof doc.labels[key], 'string');
    assert.match(page, new RegExp(`presentationLabels\\.labels\\.${key}`));
  }
  assert.match(page, /import presentationLabels from "\.\/presentationLabels\.json"/);
  assert.match(page, /Black Neoprene Jacket \(\+\$100\)/);
  assert.match(page, /setSelectedFittingType/);
});
