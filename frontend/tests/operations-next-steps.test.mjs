/** Operations next-step rules (request progress bar and Overview "Needs you"). */
import assert from 'node:assert/strict';
import {
  requestNextStepSummary as requestNext,
  orderNextStep as orderNext,
} from '../src/components/operations/operationsNextSteps.ts';

const quote = (status, formalQuotes = []) => ({ status, email: 'c@example.test', formal_quotes: formalQuotes });
const formal = (status, extra = {}) => ({
  status, revision_number: 1, staff_review_required: false, staff_review_completed_at: null, ...extra,
});

// Requests: the operator's next move, or waiting on the customer.
assert.deepEqual(requestNext(quote('new')), { label: 'Contact the customer', waiting: false });
assert.deepEqual(requestNext(quote('contacted')), { label: 'Build a formal quote', waiting: false });
assert.deepEqual(
  requestNext(quote('contacted', [formal('draft', { staff_review_required: true })])),
  { label: 'Staff review the quote', waiting: false },
);
assert.deepEqual(requestNext(quote('contacted', [formal('draft')])), { label: 'Present the quote', waiting: false });
assert.equal(requestNext(quote('quoted', [formal('presented')])).waiting, true);
assert.deepEqual(requestNext(quote('quoted', [formal('approved')])), { label: 'Close the request', waiting: false });
assert.equal(requestNext(quote('closed')), null);

// Orders: only paid, live orders; cancellation and review come before fulfilment.
const order = (overrides = {}, review = {}) => ({
  status: 'paid',
  customer_status: 'processing',
  fulfillment_status: 'not_started',
  cancellation: null,
  order_confirmation: { status: 'sent' },
  ...overrides,
  review: { status: 'reviewed', on_hold: false, ...review },
});

assert.equal(orderNext(order({ status: 'pending' })), null);
assert.equal(orderNext(order({ customer_status: 'cancelled' })), null);
assert.equal(orderNext(order({ fulfillment_status: 'delivered' })), null);
assert.equal(orderNext(order({ cancellation: { status: 'requested' } }, { status: 'pending' })).action, 'Review the cancellation request');
assert.deepEqual(orderNext(order({}, { on_hold: true })), { action: 'On hold, waiting for the customer', waiting: true });
assert.equal(orderNext(order({}, { status: 'pending' })).action, 'Review the order');
assert.equal(orderNext(order({ order_confirmation: { status: 'failed' } })).action, 'Resend the order confirmation');
assert.deepEqual(orderNext(order()), { action: 'Order from the supplier', waiting: false });
assert.equal(orderNext(order({ fulfillment_status: 'supplier_ordered' })).waiting, true);
assert.deepEqual(orderNext(order({ fulfillment_status: 'received_ready' })), { action: 'Ship the order', waiting: false });
assert.equal(orderNext(order({ fulfillment_status: 'shipped' })).waiting, true);

console.log('Operations next steps: PASS.');
