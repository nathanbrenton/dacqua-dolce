# PT41 — Order Lifecycle, Supplier Confirmation, and Cancellation Guardrails

PT41 aligns the customer-facing order lifecycle with the client-approved launch
model while preserving the existing internal payment and fulfillment state
machines.

## Customer-visible lifecycle

The customer-facing order status is derived from durable internal state:

- `Received` — the order exists but payment has not yet been confirmed.
- `Processing` — payment is confirmed and D'Acqua Dolce is preparing the order.
- `Supplier Confirmed` — D'Acqua Dolce records the supplier-confirmation boundary.
- `Awaiting Shipment` — the equipment is received/ready and is being prepared for shipment.
- `Shipped` — carrier/tracking evidence is recorded.
- `Completed` — delivery is recorded.

Cancelled and refunded orders remain explicit terminal states.

The existing database enum values remain unchanged. In particular,
`fulfillment_status = supplier_ordered` is retained as the durable implementation
state for compatibility, but its customer-facing meaning is now `Supplier Confirmed`.
This avoids an unnecessary enum migration while preserving historical records.

## Supplier-confirmation boundary

The transition from `not_started` to `supplier_ordered` is the authoritative
customer-facing Supplier Confirmed action. Operations clearly warns staff that
marking this state closes the normal online cancellation path.

The existing `supplier_ordered_at` timestamp remains the durable historical
boundary field. Its database name is retained for compatibility.

PT41 does not automatically send a supplier-confirmation email. The confirmed
status is visible in the customer account, and future transactional-message
commissioning can use the same audited transition without redefining the boundary.

## Cancellation behavior

Before Supplier Confirmed:

- the customer may submit an online cancellation;
- the request remains automatically approved in the existing cancellation
  workflow;
- an active cancellation blocks Supplier Confirmed.

After Supplier Confirmed:

- the normal customer online cancellation action is closed;
- the customer is directed to contact D'Acqua Dolce if exceptional review is
  needed;
- the customer API enforces the same boundary and rejects a direct post-confirmation
  cancellation request;
- manager/administrator/developer roles may start an auditable exceptional
  cancellation review in Operations;
- exceptional reviews reuse the existing `manual_review` cancellation workflow;
- payment reversal/void automation remains out of scope until the commissioned
  payment provider supports authoritative refund/void behavior.

This implements the operational boundary without publishing final legal policy
language. Final customer-facing cancellation terms still require legal review.

## Authorization

Ordinary Operations employees can view order/cancellation state but cannot create
or approve post-confirmation cancellation exceptions. Exceptional cancellation
review is limited to manager, administrator, and developer roles.

## Deferred

PT41 does not:

- publish final cancellation-policy legal prose;
- calculate cancellation/restocking/supplier fees automatically;
- issue payment-provider refunds or voids;
- automatically email Supplier Confirmed notifications;
- change the Affinity24 integration boundary.
