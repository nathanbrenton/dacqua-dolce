/** G4 adaptation of PT53: present AI galleries and preserved Origin paths. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {resolveApprovedGallery, approvedLandingPhoto} from '../src/components/catalog/productMediaRegistry.ts';
let passed=0;
for(const [sku,family] of [['DD15SOFT','refine'],['DD20SOFT','refine'],['DD15CATRV','essence'],['DD20CATRV','essence']]) {
 for(const finish of ['stainless','neoprene']) {
  const photos=resolveApprovedGallery(sku,finish);
  assert.ok(photos?.length,`${sku}/${finish}`);
  assert.equal(photos[0].id,'system');
  assert.match(photos[0].media.src,new RegExp(`/ai-placeholders/${family}/`));
  for(const photo of photos) for(const u of [photo.media.src,photo.media.thumbnail]) {
    assert.ok(fs.existsSync(path.join('public',u)),u);
  }
  assert.equal(resolveApprovedGallery(sku,finish,null,'1.5','legacy-original'),null);
  passed++;
 }
}
for(const sku of ['DD15CLEARPTV','DD15CLEARPL1','DD15CLEARPL2','DD15CLEARPL3']) {
 for(const finish of ['stainless','neoprene']) for(const size of ['1.5','2.0']) {
  const photos=resolveApprovedGallery(sku,finish,null,size);
  assert.ok(photos?.length,`${sku}/${finish}/${size}`);
  assert.match(photos[0].media.src,/ai-placeholders\/harmony\//);
  assert.equal(photos.some(x=>x.id==='pureline'),sku!=='DD15CLEARPTV');
  for(const p of photos) for(const u of [p.media.src,p.media.thumbnail])
    assert.ok(fs.existsSync(path.join('public',u)),u);
  passed++;
 }
}
assert.equal(resolveApprovedGallery('DD20CLEARPL2'),null);
for(const sku of ['DD5RO','DD6ROAE']) {
  const images=resolveApprovedGallery(sku);
  assert.equal(images.length,6);
  assert.deepEqual(resolveApprovedGallery(sku,'stainless',null,'1.5','legacy-original'),images);
  assert.equal(approvedLandingPhoto(sku),null);
  for(const p of images) for(const u of [p.media.src,p.media.thumbnail])
    assert.ok(fs.existsSync(path.join('public',u)),u);
}
const fitting='/__dd_image_preview/clack/V3007-02LF.png';
assert.equal(resolveApprovedGallery('DD15SOFT','stainless',fitting).at(-1).media.src,fitting);
assert.equal(resolveApprovedGallery('DD15SOFT','stainless',fitting).at(-1).id,'hookup');
console.log(`PASS: PT53/G4 current image galleries (${passed}), Origin, and fittings`);
