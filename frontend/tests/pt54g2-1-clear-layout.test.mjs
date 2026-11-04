import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const source = readFileSync(new URL('../src/components/catalog/ProductDetailPage.tsx', import.meta.url), 'utf8');

test('PT54-G2.1: CLEAR technology section is between configuration and installation', () => {
  const configuration = source.indexOf('{configurationFamily !== null ? (');
  const clear = source.indexOf('aria-label="About CLEAR Technology"');
  const installation = source.indexOf('{presentation.installationFacts.length > 0 ? (');
  assert.ok(configuration >= 0 && clear > configuration && installation > clear);
  assert.equal((source.match(/aria-label="About CLEAR Technology"/g) ?? []).length, 1);
  assert.equal((source.match(/\{presentation\.education !== null \? \(/g) ?? []).length, 1);
  assert.match(source, /CLEAR terminology/);
  assert.match(source, /presentation\.technologyFacts\.map/);
  assert.match(source, /presentation\.technologyGuidance/);
});

test('PT54-G2.1: G2 notices remain in gallery and Harmony configuration', () => {
  const gallery = source.indexOf('className="product-detail-gallery"');
  const copy = source.indexOf('className="product-detail-copy"');
  const productNotice = source.indexOf('<ProductImageNotice />');
  const maintenance = source.indexOf('<PureLineMaintenanceNotice />');
  const clear = source.indexOf('aria-label="About CLEAR Technology"');
  assert.ok(gallery >= 0 && productNotice > gallery && productNotice < copy);
  assert.ok(maintenance > copy && maintenance < clear);
  assert.equal((source.match(/<ProductImageNotice \/>/g) ?? []).length, 1);
  assert.equal((source.match(/<PureLineMaintenanceNotice \/>/g) ?? []).length, 1);
});
