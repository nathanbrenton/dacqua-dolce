# PT45 — Payment Provider Foundation

## Purpose

PT45 tightens the existing provider-neutral payment boundary without guessing
which concrete gateway Affinity24 will provision for D'Acqua Dolce.

Affinity24 remains the selected payment-processor direction. Its public
solutions material currently lists multiple gateway/omni-channel options,
including Authorize.Net, iPOS, FluidPay, and NMI. Selecting Affinity24 therefore
does not identify the API, webhook contract, refund semantics, or production
credentials the application should implement.

Authoritative provider references reviewed for this milestone:

- https://affinity24.com/solutions/
- https://affinity24.com/security/

## PT45 implementation

The payment-provider adapter now exposes an explicit, non-secret gateway
`PaymentProviderDescriptor` containing:

- exact gateway identity;
- sandbox versus production environment;
- hosted versus tokenized integration mode;
- authoritative contract/source reference;
- documented capabilities;
- explicit production-commissioning state.

Hosted checkout refuses to call an adapter unless the descriptor establishes:

1. hosted checkout or tokenized card entry appropriate to its integration mode;
2. authenticated provider webhooks;
3. durable provider event identifiers;
4. idempotent checkout creation;
5. explicit production commissioning when the adapter claims to be production.

The provider name returned by checkout must also match the commissioned gateway
identity. This prevents an adapter/result mismatch from silently creating a
payment reference under a different provider name.

## Refund and void boundary

PT45 introduces provider-neutral, card-data-free request/result contracts for a
future refund or pre-settlement void operation. They are deliberately not wired
to an API, customer action, Operations action, or payment event.

No refund/void capability is inferred merely because Affinity24 or a listed
gateway advertises payment processing. Exact full/partial-refund and void rules
must come from the gateway actually provisioned for D'Acqua Dolce and must be
reconciled with the business cancellation/refund workflow before activation.

## Existing safety boundaries retained

PT45 does not change these existing rules:

- D'Acqua Dolce never receives or stores PAN, CVV/CVC, expiration date, track
  data, PIN data, cardholder-authentication data, or raw provider payloads.
- Checkout uses the authoritative order total.
- PT44 automated-tax readiness remains a prerequisite to checkout.
- Provider events must be authenticated by a concrete gateway adapter before
  entering the existing `VerifiedPaymentEvent` core.
- Successful payment amount and currency must exactly match the order.
- Provider events remain idempotent by provider + durable event ID.
- Refund event semantics remain non-mutating until explicitly commissioned.

## Launch readiness

`Payment & checkout` is now `Action required`, not merely deferred. The code
foundation exists, but general production checkout cannot be considered ready
until Affinity24 supplies the exact provisioned gateway and its authoritative
integration contract.

## Required Affinity24 / gateway answers

Before PT46 can implement a concrete sandbox adapter, obtain:

- exact gateway/platform and product name;
- sandbox/test merchant account and base URL;
- authoritative developer/API documentation;
- hosted payment-page or hosted-fields/tokenization contract;
- authentication/credential names;
- webhook endpoint requirements and signature/authentication algorithm;
- replay protection and durable event identifier;
- idempotency-key behavior for checkout creation;
- success/cancel/return URL behavior;
- authoritative amount/currency fields on payment success;
- status vocabulary and asynchronous/out-of-order behavior;
- authorize/capture/sale/void/full-refund/partial-refund semantics;
- enabled payment methods for this merchant account;
- test cards/payment methods;
- test/production credential separation and rotation procedure;
- expected PCI SAQ/integration posture.

## Database

No database migration is required for PT45. The existing payment provider
reference/event tables remain the durable evidence model.
