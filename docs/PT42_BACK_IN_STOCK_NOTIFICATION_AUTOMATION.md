# PT42 — Back-in-Stock Notification Automation

## Purpose

PT42 commissions the existing **Notify When in Stock** subscription path as a
one-time transactional availability notification workflow.

The client approved automatic availability email and delegated the technical
trigger design. PT42 intentionally sends only after an authorized staff member
saves inventory in a state that confirms customer-available stock.

## Trigger

An availability notice is eligible only when an Operations inventory save
confirms all of the following:

- inventory status is `in_stock` or `low_stock`;
- on-hand quantity exceeds active cart reservations;
- product lifecycle is not `discontinued`;
- the subscription is still active.

Supplier/manufacturer observations do not independently send customer email.
The current implementation has no background inventory adapter that bypasses
the Operations write boundary.

## Delivery behavior

- Uses the existing transactional email provider boundary (`deliver_email`).
- Category: `stock_notification`.
- One successful delivery completes the one-time subscription:
  - `active = false`
  - `notified_at = <send time>`
- Failed or suppressed delivery leaves the subscription active.
- A later staff inventory save that again confirms availability may retry those
  unresolved active subscriptions.
- Successful subscriptions are not sent again unless the customer later
  creates a new active request.

This design makes normal repeated inventory saves idempotent for successfully
delivered subscriptions while still giving failed deliveries a controlled
staff-confirmed retry path.

## Customer cancellation

The product detail page provides **Cancel availability notice** using the same
email address used for the request.

The cancellation endpoint returns a generic success response whether or not an
active request exists, so it does not expose subscription existence.

Cancellation is audited without placing the customer email address in audit
metadata.

## Audit and communications evidence

Each delivery attempt:

- creates an `EmailDelivery` record through the existing email boundary;
- archives the outbound transactional email;
- records `catalog.stock_notification_delivery` audit evidence with product,
  subscription, delivery ID, and delivery status.

Subscription creation and customer cancellation also receive audit events.

## Explicit non-goals

PT42 does **not**:

- create newsletters or marketing lists;
- send recurring promotional email;
- infer availability from transient external supplier data;
- send for discontinued products;
- alter pricing, tax, payments, or shipping insurance;
- add a new inventory role (the planned inventory-specific permission remains
  a future authorization milestone).

## Production acceptance

1. Confirm an out-of-stock product can accept a Notify When in Stock request.
2. Confirm the active request appears in Operations.
3. Save the product as available with positive unreserved quantity.
4. Confirm a transactional availability email is sent.
5. Confirm the successful request leaves the active Operations queue.
6. Confirm the EmailDelivery/audit evidence exists.
7. Confirm repeating an available inventory save does not send the completed
   request again.
8. Confirm a customer can cancel an active request from the product page.
9. Confirm failed/suppressed delivery remains active for later staff retry.
