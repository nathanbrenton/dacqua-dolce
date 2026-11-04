/** G4: Origin F3 publication overlay remains; removed Refine/Essence overlay no longer routable. */
import assert from 'node:assert/strict';
import {mkdtempSync,cpSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {resolveApprovedGallery,approvedLandingPhoto} from '../src/components/catalog/productMediaRegistry.ts';
assert.equal(resolveApprovedGallery('DD5RO').length,6);
assert.equal(approvedLandingPhoto('DD15SOFT','legacy-original'),null);
const work=mkdtempSync(join(tmpdir(),'dacqua-g4-origin-f3-'));
try {
 for(const name of ['productMediaRegistry.ts','photoCaptionOverrides.json','photoSetIndex.json']) {
   cpSync(fileURLToPath(new URL(`../src/components/catalog/${name}`,import.meta.url)),join(work,name));
 }
 const fake=(configuration,role,sequence,version,stem)=>({configuration,role,sequence,version,
  photographed_valve:null,src:`/products/media/origin/generated/${stem}.webp`,
  thumbnail:`/products/media/origin/generated/thumbnails/${stem}.webp`,source_sha256:'a'.repeat(64),
  source_name:`${stem}.png`,published_utc:'2026-11-03T00:00:00Z'});
 writeFileSync(join(work,'publishedPhotoIndex.json'),JSON.stringify({schema_version:1,entries:[
  fake('origin:DD5RO','detail',3,1,'old'),fake('origin:DD5RO','detail',3,2,'new'),
  fake('origin:DD5RO','angle',4,1,'additional')]}));
 const registry=await import(pathToFileURL(join(work,'productMediaRegistry.ts')).href);
 const selected=registry.resolveApprovedGallery('DD5RO');
 assert.equal(selected.length,8);
 assert.ok(selected.some(p=>p.media.src.includes('new.webp')));
 assert.ok(!selected.some(p=>p.media.src.includes('old.webp')));
 assert.equal(registry.approvedLandingPhoto('DD15SOFT','legacy-original'),null);
 console.log('PASS: F3 Origin publications retain precedence, legacy catalog fallback stays separate');
} finally {rmSync(work,{recursive:true,force:true});}
