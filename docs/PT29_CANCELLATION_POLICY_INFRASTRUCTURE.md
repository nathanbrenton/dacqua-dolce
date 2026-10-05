# PT29 — Cancellation Policy Infrastructure

## Purpose

PT29 implements the confirmed launch cancellation boundary without inventing
post-confirmation fees, refund behavior, or payment-provider capabilities.

Confirmed business direction at PT29 was later refined by PT41:

- A customer cancellation is unrestricted until D'Acqua Dolce records Supplier Confirmed.
- After Supplier Confirmed, the normal online customer cancellation path is closed.
- An authorized privileged staff member may start a case-by-case exceptional review.
- Final customer-facing legal wording still requires legal review.
- Payment-provider refund/void automation remains deferred until the Affinity24
  gateway and authoritative integration contract are known.

## Authoritative supplier-confirmation boundary

The application already records supplier confirmation through the fulfillment
transition to `supplier_ordered`. That transition stamps `supplier_ordered_at`.

PT29 uses that durable fulfillment state rather than UI text:

- `fulfillment_status = not_started` and `supplier_ordered_at IS NULL`
  → cancellation mode `unrestricted`.
- supplier confirmation or any later fulfillment state
  → customer cancellation mode `closed_after_supplier_confirmation`.

The stored `manual_review` eligibility value remains available for auditable
post-confirmation exceptions and for historical PT29 records.

## Cancellation workflow

PT29 adds one durable cancellation workflow record per order.

Statuses:

- `requested` — an authorized post-confirmation exception is waiting for review.
- `approved` — cancellation has been accepted. Pre-supplier requests enter this
  state automatically because cancellation is unrestricted at that point.
- `declined` — a post-supplier manual review did not approve cancellation.
- `completed` — Operations confirms the cancellation workflow has been completed
  after any required manual payment/administrative actions.

The cancellation record does not claim that a payment has been refunded or
voided.

## Fulfillment safety

An active pre-supplier cancellation blocks the transition from `not_started` to
`supplier_ordered`.

An active cancellation also prevents a new hosted checkout session from being
created for an order that is still awaiting payment.

A declined cancellation permits checkout/fulfillment to continue when the
order is otherwise eligible.

Post-supplier cancellation requests do not automatically reverse or mutate
existing fulfillment history.

## Payment boundary

PT29 intentionally keeps cancellation workflow state separate from
`orders.status` and payment-provider state.

The current payment architecture explicitly defers full/partial refund
semantics until the actual Affinity24-backed provider integration is
commissioned. Therefore PT29 does not:

- issue a refund or void;
- mutate payment-provider references;
- claim a refund succeeded;
- automatically set a paid order to `cancelled` or `refunded`.

Operations can mark the cancellation workflow complete only after any required
manual payment or administrative work has been handled outside the automated
provider path.

## Customer experience

Customer Account order history exposes:

- current cancellation mode;
- current cancellation-request state;
- an optional cancellation reason;
- a pre-Supplier-Confirmed `Cancel order` action;
- after Supplier Confirmed, a clear message that the online cancellation path is closed and the customer should contact D'Acqua Dolce for exceptional review.

Internal supplier order references remain excluded from customer responses.

## Operations experience

Operations order controls expose:

- cancellation mode and request status;
- customer-provided reason;
- an authorized post-confirmation exceptional-review action for privileged staff;
- optional review note;
- Approve / Decline controls for exceptional manual-review requests;
- Mark cancellation complete for approved requests;
- a Supplier Confirmed block while a pre-confirmation cancellation remains active.

All state changes are audited without storing the customer's free-text reason in
audit metadata.

## Existing policy/version system

The Cancellation Policy remains one of the required approved policy snapshots
attached to newly presented formal quotes.

PT29 does not generate or approve legal policy text and does not change the
Draft → Approved → Retired policy lifecycle.

## Explicitly deferred

The following remain outside PT29:

- automatic cancellation fees;
- a detailed post-supplier-confirmation cancellation matrix;
- automatic payment refund/void behavior;
- partial refund semantics;
- shipping-insurance behavior;
- return/RMA execution;
- Affinity24-specific gateway calls.

Those items should be implemented only after the required business, legal,
manufacturer, or payment-provider facts are available.
