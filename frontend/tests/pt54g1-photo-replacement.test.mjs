/** PT54-G4: new G1 AI index and original catalog fallback, fitting/Origin preservation. */
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolveApprovedGallery,approvedLandingPhoto,AVAILABLE_PHOTO_SOURCES,DEFAULT_PHOTO_SOURCE} from '../src/components/catalog/productMediaRegistry.ts';
const index=JSON.parse(readFileSync(new URL('../src/components/catalog/photoSetIndex.json',import.meta.url)));
const menu=readFileSync(new URL('../src/components/developer/DeveloperControls.tsx',import.meta.url),'utf8');
assert.equal(index.schema_version,1);
assert.equal(DEFAULT_PHOTO_SOURCE,'ai-placeholder');
assert.match(menu,/developer-photo-source/);
assert.match(menu,/Original \/ legacy catalog photography/);
assert.equal(AVAILABLE_PHOTO_SOURCES['product-photo'],false);
assert.equal(AVAILABLE_PHOTO_SOURCES['legacy-original'],true);
assert.equal(index.sets['product-photo'].active,false);
assert.equal(resolveApprovedGallery('DD5RO')?.length,6);
assert.equal(resolveApprovedGallery('DD6ROAE')?.length,6);
if(index.sets['ai-placeholder'].active){
 const entries=index.sets['ai-placeholder'].entries;
 assert.equal(Object.keys(entries).length,24);
 for(const [key,photos] of Object.entries(entries)){
  assert.ok(photos.length>0,key);
  assert.equal(new Set(photos.map(x=>x.id)).size,photos.length,key);
  for(const photo of photos){
   assert.match(photo.media.src,/^\/products\/media\/ai-placeholders\//);
   assert.match(photo.media.thumbnail,/\/ai-placeholders\/.*\/thumbnails\//);
   for(const url of [photo.media.src,photo.media.thumbnail])
    assert.ok(existsSync(fileURLToPath(new URL(`../public${url}`,import.meta.url))),url);
  }
 }
 for(const [sku,family] of [['DD15SOFT','refine'],['DD20SOFT','refine'],
  ['DD15CATRV','essence'],['DD20CATRV','essence'],['DD15CLEARPL2','harmony']]) {
  assert.match(approvedLandingPhoto(sku)?.media.src,new RegExp(`/ai-placeholders/${family}/`));
  assert.equal(approvedLandingPhoto(sku,'legacy-original'),null);
 }
 const fitting='/__dd_fitting/example.webp';
 const gallery=resolveApprovedGallery('DD15SOFT','stainless',fitting);
 assert.equal(gallery.at(-1).id,'hookup');
 assert.equal(gallery.at(-1).media.src,fitting);
 assert.equal(gallery.length,5);
 assert.equal(resolveApprovedGallery('DD15CLEARPL2','neoprene',null,'2.0')?.length,4);
}
console.log('PASS: G1/G4 current AI, original source, fittings and RO');
