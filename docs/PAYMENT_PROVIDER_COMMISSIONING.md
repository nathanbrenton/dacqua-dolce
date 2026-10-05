# D'Acqua Dolce Payment Provider Commissioning Checklist

## Purpose

This checklist is the handoff between the provider-neutral payment architecture
and the exact gateway Affinity24 provisions for D'Acqua Dolce. It contains no
credentials and should remain safe to keep in Git.

## Required provider facts

Record authoritative answers before implementing the production adapter:

- exact gateway/platform and product name;
- sandbox/test availability and base URL;
- production base URL;
- hosted payment page/session API documentation;
- API authentication method and exact credential names;
- webhook endpoint requirements;
- webhook authentication/signature algorithm and replay protections;
- durable provider event identifier;
- checkout/session identifier and payment/transaction identifier;
- provider payment-status vocabulary and transition semantics;
- whether events may arrive out of order or be retried;
- idempotency-key support and retry behavior for checkout creation;
- success/cancel/return URL behavior;
- authoritative amount and currency fields on successful payment events;
- refund and void semantics, including partial refunds;
- payment methods enabled for this merchant account, including ACH if offered;
- provider fields that may be retained for operational display;
- test cards/test payment methods supplied by the gateway;
- go-live credential/endpoint separation and rotation procedure.

## D'Acqua Dolce invariants

Regardless of gateway, the adapter must preserve these rules:

1. Card data is entered only on the contracted provider's PCI-compliant hosted
   or tokenized surface.
2. D'Acqua Dolce never receives or stores PAN, CVV/CVC, expiration date, track
   data, PIN data, cardholder-authentication data, or raw provider payloads.
3. Checkout creation remains server-side and uses the authoritative order total.
4. Provider webhooks are authenticated before normalization.
5. Provider events are idempotent by a durable provider event ID.
6. A successful payment cannot mark an order paid unless amount and currency
   exactly match the authoritative order.
7. An event for one provider/payment reference cannot be rebound to another.
8. Late failure/cancellation signals cannot regress an already successful payment.
9. Refund behavior is commissioned explicitly; it is not inferred from marketing
   documentation or a generic status label.
10. Production checkout stays disabled until sandbox success, webhook validation,
    retry/idempotency tests, and controlled production acceptance are complete.

## Acceptance sequence

When provider documentation is available, implement and validate in this order:

1. provider-specific configuration with disabled-by-default production behavior;
2. sandbox hosted-checkout adapter;
3. authenticated webhook endpoint and signature/replay verification;
4. normalization into the existing verified-payment-event core;
5. success, failure, cancel, retry, duplicate, out-of-order, and amount-mismatch tests;
6. refund/void behavior after business policy is confirmed;
7. customer account redirect/return UX;
8. controlled sandbox end-to-end payment;
9. production credentials and endpoint commissioning;
10. one controlled production acceptance transaction before general availability.

## PT45 gateway-contract enforcement

PT45 converts several checklist items above into executable adapter
requirements. A concrete payment adapter must expose a non-secret descriptor
containing its exact gateway identity, environment, integration mode,
authoritative source reference, documented capabilities, and explicit
production-commissioning state.

Before checkout orchestration will call the provider, that descriptor must
establish hosted/tokenized card entry, authenticated webhooks, durable event
identifiers, and idempotent checkout creation. A production descriptor is also
rejected unless it has been explicitly commissioned.

The checkout result must identify the same gateway as the descriptor. Refund
and void request/result interfaces now exist as provider-neutral boundaries but
are intentionally not callable by customers or staff until the exact provisioned
gateway contract and business refund workflow are reconciled.

Affinity24's public solutions page currently lists Authorize.Net, iPOS,
FluidPay, and NMI as gateway/omni-channel options. That public list is evidence
that the exact provisioned gateway must be obtained from merchant onboarding;
it is not permission to choose one in code.
