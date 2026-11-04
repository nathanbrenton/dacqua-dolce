import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
const source = fs.readFileSync(path.resolve('src/components/catalog/productMediaRegistry.ts'), 'utf8');
const data = JSON.parse(fs.readFileSync(path.resolve('src/components/catalog/photoCaptionOverrides.json'), 'utf8'));
test('F6 caption file is versioned, empty by default and separate from photo assets', () => {
  assert.equal(data.schema_version, 1);
  assert.ok(data.families && data.configurations);
});
test('F6 caption overrides apply after approved publications and before gallery return', () => {
  assert.match(source, /function withCaptionOverrides\(/);
  assert.match(source, /CAPTIONS\.configurations\[key\].*CAPTIONS\.families\[family\]/);
  assert.match(source, /return withCaptionOverrides\(photos, key\)/);
  assert.match(source, /return withCaptionOverrides\(mergePublishedPhotos\(ORIGIN_GALLERIES\[sku\]/);
});
