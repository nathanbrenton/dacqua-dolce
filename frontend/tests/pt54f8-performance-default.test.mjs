/** G4 replaces F8: current AI photographs depict Performance valves only. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {approvedLandingPhoto,DEFAULT_PHOTO_SOURCE} from '../src/components/catalog/productMediaRegistry.ts';
const read=n=>readFileSync(new URL('../src/'+n,import.meta.url),'utf8');
const menu=read('components/developer/DeveloperControls.tsx');
const registry=read('components/catalog/productMediaRegistry.ts');
const app=read('App.tsx');
assert.equal(DEFAULT_PHOTO_SOURCE,'ai-placeholder');
assert.doesNotMatch(menu,/developer-photo-valve|Use Archetype photoset/);
assert.doesNotMatch(app,/imagePreviewEnabled|photoValve/);
assert.doesNotMatch(registry,/PHOTO_REGISTRY|DEFAULT_PHOTO_VALVE|TreatmentValve|Photoset/);
for(const sku of ['DD15SOFT','DD20SOFT','DD15CATRV','DD20CATRV'])
 assert.match(approvedLandingPhoto(sku).media.src,/performance/);
console.log('PASS: G4 removes obsolete presentation-valve/photoset switching');
