/** PT54-G2 — exact legal copy; two placements; one instance per product detail. */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
const file = (name) => readFileSync(new URL(name, import.meta.url), 'utf8');
const copy = JSON.parse(file('../src/components/catalog/productNotices.json'));
const page = file('../src/components/catalog/ProductDetailPage.tsx');
const components = file('../src/components/catalog/ProductContentNotices.tsx');
const stylesheet = file('../src/components/catalog/ProductContentNotices.css');

test('exact customer-approved disclaimer language is centralized', () => {
  assert.equal(copy.schema_version,1);
  assert.equal(copy.product_image_disclaimer,
    "Product images may vary slightly from the actual product received. Variations in appearance, color, finish, or component design may occur without affecting the product's intended functionality or performance.");
  assert.equal(`${copy.pureline_maintenance_heading} ${copy.pureline_maintenance_body}`,
    'Important Maintenance Notice: PureLine filter cartridges must be replaced according to the recommended maintenance schedule. Failure to replace cartridges in a timely manner may cause certain filter media to soften, deteriorate, or disintegrate, potentially resulting in plumbing blockages, equipment malfunction, or damage to the plumbing system.');
});

test('product-image notice follows gallery regardless of family or image availability', () => {
  assert.equal((page.match(/<ProductImageNotice\s*\/>/g) ?? []).length,1);
  assert.match(page, /className="product-detail-gallery"[\s\S]*?<ProductImageNotice\s*\/>[\s\S]*?<\/div>[\s\S]*?<div className="product-detail-copy">/);
  assert.match(components, /aria-label="Product image disclaimer"/);
});

test('PureLine warning only appears on Harmony pages and does not repeat', () => {
  assert.equal((page.match(/<PureLineMaintenanceNotice\s*\/>/g) ?? []).length,1);
  assert.match(page, /\{isHarmony \? <PureLineMaintenanceNotice \/> : null\}/);
  assert.match(components, /aria-label="PureLine maintenance notice"/);
  assert.match(components, /<strong>\{notices\.pureline_maintenance_heading\}<\/strong>/);
});

test('presentational styles inherit main website themes', () => {
  assert.match(components,/import "\.\/ProductContentNotices\.css";/);
  assert.match(stylesheet,/color:\s*inherit/);
  assert.doesNotMatch(stylesheet, /#[0-9a-fA-F]{3,8}/);
  assert.doesNotMatch(page, /const\s+.*(?:notice|disclaimer).*price/i);
});
