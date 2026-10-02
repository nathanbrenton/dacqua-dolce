# PT33 — Shipping Insurance Acceptance / Refusal Evidence

## Scope

PT33 records a customer's explicit shipping-insurance choice against one
presented formal-quote revision.

A presented quote that contains a positive `shipping_insurance` commercial
charge exposes two choices:

- `accepted`
- `declined`

The latest pre-approval choice is stored on the formal quote with a timestamp
and the customer's user-ID snapshot. Every change is also audit logged.

Once the quote is approved, the quote is no longer `presented`, so this evidence
cannot be changed through the customer decision endpoint.

## Approval invariant

A quote with a positive shipping-insurance charge cannot be approved until the
customer has accepted shipping insurance.

If the customer declines, that refusal is retained on the presented revision.
The quote cannot be approved while the insurance charge remains present.
D'Acqua Dolce must prepare a new quote revision without the insurance charge
before the customer can approve commercial terms.

This avoids changing an immutable presented quote total or producing an order
whose price contradicts the customer's insurance choice.

Quotes without a shipping-insurance charge require no insurance decision.

## Evidence and visibility

Customer Account and Operations both expose:

- whether shipping insurance was offered on the quote;
- the current `accepted` / `declined` choice;
- when that choice was recorded.

The `formal_quote.approved` audit event also includes the accepted insurance
decision, timestamp, amount, and currency when applicable.

## Intentionally deferred

PT33 does not define or imply:

- an insurer or insurance provider;
- policy or coverage wording;
- premium calculation or carrier rating;
- carrier-damage claims handling;
- legal interpretation of risk of loss;
- refunds or claim proceeds;
- Affinity24 settlement behavior.

Those items require provider and/or legal terms before implementation.
