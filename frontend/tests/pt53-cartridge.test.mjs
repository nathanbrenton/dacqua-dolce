/** PT53 Harmony cartridge regression checks; run from frontend with Node >=22.18. */
import assert from 'node:assert/strict';
// Native TypeScript type stripping works with TypeScript 7 and needs no extra dependency.
import {
  HARMONY_CARTRIDGES as values,
  validCartridgeChoices as valid,
  harmonyHousingCountForSku as housingCount,
  validHousingSelections as validHousing,
  PURELINE_HOUSINGS as housings,
} from '../src/components/catalog/harmonyCartridges.ts';

assert.equal(values.sediment.length, 10);
assert.equal(values.carbon.length, 3);
assert.equal(values.iron.length, 1);
assert.equal(housingCount('DD15CLEARPL1'), 1);
assert.equal(housingCount('DD15CLEARPL2'), 2);
assert.equal(housingCount('DD15CLEARPL3'), 3);
assert.equal(housingCount('DD15CLEARPTV'), 0);
assert.deepEqual(housings, ['housing1', 'housing2', 'housing3']);
assert.ok(validHousing({ housing1: { category:'sediment', cartridge: values.sediment[0], otherDescription:'' },
  housing2: { category:'sediment', cartridge: values.sediment[2], otherDescription:'' } }));
assert.ok(validHousing({ housing1: { category:'other', cartridge:'', otherDescription:'bone char inquiry' } }));
assert.equal(validHousing({ housing1: { category:'carbon', cartridge: values.sediment[0], otherDescription:'' } }), false);
assert.equal(validHousing({ housing1: { category:'iron', cartridge:'Invented iron media', otherDescription:'' } }), false);
assert.ok(valid({ sediment: values.sediment[0], carbon: values.carbon[1] }));
assert.equal(valid({ sediment: 'Invented 100 micron cartridge' }), false);
console.log('PT53 Harmony cartridge options: PASS.');
