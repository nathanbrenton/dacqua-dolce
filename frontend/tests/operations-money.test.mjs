/** Operations dollar inputs and request message splitting. */
import assert from 'node:assert/strict';
import {
  normalizeDollarInput,
  parseDollarsToMinor,
  splitRequestMessage,
} from '../src/components/operations/operationsMoney.ts';

assert.equal(parseDollarsToMinor('2500.00'), 250000);
assert.equal(parseDollarsToMinor('$2500.00'), 250000);
assert.equal(parseDollarsToMinor(' $ 2,499.5 '), 249950);
assert.equal(parseDollarsToMinor('2500'), 250000);
assert.equal(parseDollarsToMinor(''), null);
assert.equal(parseDollarsToMinor('$'), null);
assert.equal(normalizeDollarInput('$1,000'), '1000');
assert.throws(() => parseDollarsToMinor('25.999'));
assert.throws(() => parseDollarsToMinor('-5'));
assert.throws(() => parseDollarsToMinor('USD 5'));

const config = 'Customer-requested configuration (NOT a priced or approved order):\nCatalog reference SKU: X (Harmony)';
assert.deepEqual(splitRequestMessage(`${config}\n\nHello there`), { configuration: config, customerMessage: 'Hello there' });
assert.deepEqual(splitRequestMessage(config), { configuration: config, customerMessage: null });
assert.deepEqual(splitRequestMessage('Just a note'), { configuration: null, customerMessage: 'Just a note' });
assert.deepEqual(splitRequestMessage(null), { configuration: null, customerMessage: null });

console.log('Operations money and request message: PASS.');
