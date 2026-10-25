/** PT53 registry regression checks; run from frontend with Node >=22.18. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
// Node's built-in TypeScript type stripping avoids the removed TypeScript 7 compiler API.
import { resolveApprovedGallery, approvedLandingPhoto } from '../src/components/catalog/productMediaRegistry.ts';

let passed = 0;
for (const skus of [['DD15SOFT', 'DD20SOFT'], ['DD15CATRV', 'DD20CATRV']]) {
  for (const sku of skus) for (const finish of ['stainless', 'neoprene']) {
    for (const valve of ['clack', 'performance']) for (const photoset of ['realistic', 'archetype']) {
      const photos = resolveApprovedGallery(sku, finish, valve, photoset);
      assert.ok(photos?.length > 0, `${sku} ${finish} ${valve} ${photoset}`);
      assert.ok(photos.some(p => p.id === 'system'));
      assert.equal(photos.some(p => p.id === 'brine'), sku.includes('SOFT'));
      assert.equal(photos.some(p => p.id === 'tank'), sku.includes('SOFT'));
      for (const photo of photos) for (const url of [photo.media.src, photo.media.thumbnail]) {
        assert.ok(url.startsWith('/products/media/'), url);
        assert.ok(fs.existsSync(path.join('public', url)), `Missing asset ${url}`);
      }
      passed++;
    }
  }
}
for (const sku of ['DD15CLEARPTV', 'DD15CLEARPL1', 'DD15CLEARPL2', 'DD15CLEARPL3']) {
  for (const finish of ['stainless', 'neoprene']) {
    const realistic = resolveApprovedGallery(sku, finish, 'clack', 'realistic');
    const archetype = resolveApprovedGallery(sku, finish, 'performance', 'archetype');
    assert.ok(realistic && archetype);
    assert.deepEqual(realistic.map(p=>p.media.src), archetype.map(p=>p.media.src));
    assert.equal(realistic.some(p=>p.id === 'pureline'), sku !== 'DD15CLEARPTV');
    for(const photo of realistic) for(const url of [photo.media.src, photo.media.thumbnail])
      assert.ok(fs.existsSync(path.join('public', url)), url);
    passed += 2;
  }
}
for (const sku of ['DD15CLEARPTV', 'DD15CLEARPL1', 'DD15CLEARPL2', 'DD15CLEARPL3']) {
  for (const finish of ['stainless', 'neoprene']) {
    for (const photoset of ['realistic', 'archetype']) {
      const photos = resolveApprovedGallery(sku, finish, 'clack', photoset, null, '2.0');
      assert.ok(photos?.length, `Missing Harmony 2.0 ${sku} ${finish} ${photoset}`);
      assert.ok(photos[0].media.src.includes('harmony_2-0'));
      for (const photo of photos) for (const url of [photo.media.src, photo.media.thumbnail]) {
        assert.ok(fs.existsSync(path.join('public', url)), `Missing 2.0 Harmony asset ${url}`);
      }
      passed++;
    }
  }
}
// New 2.0 sizes use an explicit photography override on a real 1.5 cf catalog SKU.
assert.equal(resolveApprovedGallery('DD20CLEARPL2'), null, 'No invented 2.0 SKU');
// PT53 regression: both Origin variants retain all old preview photographs AND their catalog diagrams.
for (const [sku, count] of [['DD5RO', 6], ['DD6ROAE', 6]]) {
  const realistic = resolveApprovedGallery(sku, 'stainless', 'clack', 'realistic');
  const archetype = resolveApprovedGallery(sku, 'stainless', 'performance', 'archetype');
  assert.equal(realistic?.length, count, `${sku} gallery image count`);
  assert.deepEqual(realistic?.map(p => p.media.src), archetype?.map(p => p.media.src));
  for (const photo of realistic) for (const url of [photo.media.src, photo.media.thumbnail]) {
    assert.ok(url.startsWith('/products/media/'), url);
    assert.ok(fs.existsSync(path.join('public', url)), `Missing Origin asset ${url}`);
  }
  assert.equal(approvedLandingPhoto(sku, 'realistic'), null, 'Origin landing image unchanged');
}

assert.ok(approvedLandingPhoto('DD15CLEARPL2', 'realistic'));
const galleryWithFitting = resolveApprovedGallery('DD15SOFT', 'stainless', 'clack', 'realistic', '/__dd_image_preview/clack/V3007-02LF.png');
assert.ok(galleryWithFitting?.some(p=>p.id==='hookup'));
assert.equal(galleryWithFitting?.find(p=>p.id==='hookup')?.media.src,'/__dd_image_preview/clack/V3007-02LF.png');
const fittingInArchetype = resolveApprovedGallery('DD15SOFT', 'stainless', 'clack', 'archetype', '/__dd_image_preview/clack/V3007-02LF.png');
assert.equal(fittingInArchetype?.find(p=>p.id==='hookup')?.media.src, galleryWithFitting?.find(p=>p.id==='hookup')?.media.src);
console.log(`PT53 photo registry: PASS (${passed} valid photo/finish/valve/size combinations).`);
