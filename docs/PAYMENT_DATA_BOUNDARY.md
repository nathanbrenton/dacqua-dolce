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
