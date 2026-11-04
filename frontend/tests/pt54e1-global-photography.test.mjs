/** G4: only current AI and original catalog photographs may be selected. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {approvedLandingPhoto,resolveApprovedGallery,AVAILABLE_PHOTO_SOURCES} from '../src/components/catalog/productMediaRegistry.ts';
const read=n=>readFileSync(new URL('../src/'+n,import.meta.url),'utf8');
const app=read('App.tsx'),menu=read('components/developer/DeveloperControls.tsx');
const detail=read('components/catalog/ProductDetailPage.tsx'),cards=read('components/catalog/CatalogSection.tsx');
assert.match(menu,/developer-photo-source/);
assert.match(menu,/Original \/ legacy catalog photography/);
assert.doesNotMatch(menu,/developer-photo-valve|developer-imagery-preview-checkbox|Use Archetype/);
assert.match(app,/photoSource=\{photoSource\}/);
assert.match(cards,/photoSource=\{photoSource\}/);
assert.match(detail,/product\.sku, tankFinish,/);
assert.match(detail,/valve: valveSelectable \? "clack" : null/);
assert.doesNotMatch(detail,/valve: valveSelectable \? photoSource/);
assert.equal(AVAILABLE_PHOTO_SOURCES['legacy-original'],true);
for(const sku of ['DD15SOFT','DD20SOFT','DD15CATRV','DD20CATRV','DD15CLEARPL2']) {
  const card=approvedLandingPhoto(sku);
  assert.ok(card?.media.src.includes('/ai-placeholders/'));
  assert.equal(approvedLandingPhoto(sku,'legacy-original'),null);
  assert.equal(resolveApprovedGallery(sku,'stainless',null,'1.5','legacy-original'),null);
}
assert.equal(approvedLandingPhoto('DD5RO'),null);
console.log('PASS: PT54-G4 AI/original only; price and fittings isolated');
