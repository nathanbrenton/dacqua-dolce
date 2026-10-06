# PT47 — Employee-controlled Order Confirmed communication

PT47 implements the initial customer order-confirmation workflow approved after PT46.

## Customer communication boundary

`Supplier Confirmed` remains the internal/customer lifecycle stage introduced by PT41 and remains the normal customer cancellation boundary. Changing fulfillment to that stage does **not** automatically send email.

After staff reviews the order, an Operations user explicitly sends a separate customer-facing transactional message whose subject/heading is **Order Confirmed**.

## Delivery and evidence

The send path reuses the existing transactional email boundary and communications archive:

- category: `order_confirmation`
- related entity: the immutable D'Acqua Dolce order ID
- customer/user linkage is archived
- the staff author is recorded
- `EmailDelivery` retains delivery status/evidence
- the existing communications archive retains the outbound message
- an audit event records the delivery ID and bounded delivery status

A successfully sent confirmation is one-time. Failed or suppressed delivery attempts may be retried explicitly by staff.

## Guardrails

PT47 rejects confirmation attempts:

- before Supplier Confirmed has been recorded;
- after the order is cancelled;
- after the order is refunded; or
- when an Order Confirmed message was already sent successfully.

No automatic confirmation send is introduced. Future automation requires a separate approved milestone.

## Out of scope

PT47 does not change payment, Affinity24, automated tax, legal-policy text, shipping insurance, or the public catalog/discontinued-product lifecycle. The discontinued-product public-retirement workflow is intentionally left for the next narrow milestone after PT47 acceptance.
