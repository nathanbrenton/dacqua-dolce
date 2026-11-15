/** Preferred contact method helpers shared by the quote, support and profile forms. */
import assert from 'node:assert/strict';
import {
  CONTACT_METHOD_OPTIONS,
  DEFAULT_CONTACT_METHOD,
  contactMethodFollowUp,
  contactMethodHint,
  contactMethodLabel,
  contactMethodNeedsPhone,
  isContactMethod,
} from '../src/utils/contactMethod.ts';

assert.deepEqual(CONTACT_METHOD_OPTIONS.map((option) => option.value), ['email', 'call', 'text']);
assert.equal(DEFAULT_CONTACT_METHOD, 'email');
assert.equal(contactMethodNeedsPhone('email'), false);
assert.equal(contactMethodNeedsPhone('call'), true);
assert.equal(contactMethodNeedsPhone('text'), true);
assert.equal(contactMethodLabel('text'), 'Text message');
assert.equal(contactMethodLabel(null), null);
assert.equal(isContactMethod('call'), true);
assert.equal(isContactMethod('fax'), false);
assert.match(contactMethodHint('text'), /Message and data rates may apply/);
assert.equal(contactMethodFollowUp('email'), 'reply by email');
assert.equal(contactMethodFollowUp('text'), 'text you');
assert.equal(contactMethodFollowUp('call'), 'call you');

console.log('Contact method helpers: PASS.');
