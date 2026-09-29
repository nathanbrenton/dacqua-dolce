# D'Acqua Dolce Payment-Data Boundary

## P0 rule

Payment-card entry and processing must occur only on the contracted
PCI-compliant third-party provider's hosted or tokenized payment surface.

The D'Acqua Dolce application must never receive, transmit, log, or store:

- full PAN / card number;
- CVV / CVC / security code;
- magnetic-stripe or track data;
- PIN or PIN blocks;
- card expiration dates;
- cardholder authentication data;
- raw processor/provider payment payloads.

## Data the application may retain

Only provider-issued references and minimal display metadata required for
business operations may be retained, such as:

- provider name;
- provider checkout/session identifier;
- provider payment identifier;
- provider customer identifier;
- payment method type;
- card/network brand if supplied;
- last four digits if supplied;
- provider payment status.

## Architecture

    Browser
      |
      | order/checkout request without card data
      v
    D'Acqua Dolce FastAPI
      |
      | safe CheckoutSessionRequest
      v
    Contracted PCI provider
      |
      | hosted/tokenized card-entry surface
      v
    Customer enters payment data directly with provider

D'Acqua Dolce receives only provider-issued identifiers/status metadata
permitted by this boundary.

## Source-code guard

`backend/tests/test_payment_boundary.py` checks that the checkout request
contract and payment reference schema do not expose common prohibited
card-data field names.

This test is defense-in-depth, not a substitute for architecture review,
provider documentation, logging review, and PCI governance.

## PT16.9 provider direction — Affinity 24

The client has selected **Affinity 24** as the intended payment-provider direction. This selection does not itself commission production payments.

Before implementation, obtain and review authoritative Affinity 24 integration documentation covering the hosted/tokenized payment surface, sandbox/test environment, server-side authentication, webhook/event verification, idempotency, refund/status semantics, and the exact provider references that may be retained. The P0 card-data boundary above remains unchanged: D'Acqua Dolce must not receive or store raw card data.

## PT20.1 approved-quote handoff

PT20.1 connects the assisted-sales workflow to the payment boundary without pretending that the provider-specific integration is known. Customer approval of a formal quote now creates exactly one `awaiting_payment` order whose lines are copied from the approved quote snapshot. The order retains a unique link to that exact quote revision.

The provider-neutral hosted-checkout orchestration accepts only safe commercial context: internal order ID, amount, currency, customer email, success/cancel return URLs, and a deterministic idempotency key. It stores only the provider name and provider-issued checkout reference before a later provider event establishes payment status. Redirect URLs are not persisted as payment credentials or card data.

Affinity24 advertises hosted payment pages and tokenized vaults for card-not-present transactions, but also lists multiple gateway/omni-channel options. Therefore the production adapter remains deliberately unimplemented until D'Acqua Dolce's merchant onboarding identifies the actual gateway and supplies its authoritative sandbox/API/webhook contract.
