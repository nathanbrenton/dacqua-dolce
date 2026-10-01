# PT28 — Structured Return and Restocking Policy Infrastructure

## Purpose

PT28 records return/restocking decisions as versioned structured policy data without
inventing the launch values that remain unresolved.

The existing customer-facing policy lifecycle remains authoritative:

- `draft`
- `approved`
- `retired`

A Refund Policy may now optionally carry machine-readable structured terms alongside
its human-readable legal text. Drafts can omit structured terms while the business or
legal review is still unresolved.

## Supported structured refund terms

The Refund Policy can record:

- return eligibility mode:
  - fixed window;
  - case-by-case;
  - fixed window with case-by-case exception;
- the fixed return-window length when applicable;
- restocking mode:
  - fixed percentage;
  - case-by-case;
- the fixed restocking percentage when applicable;
- merchandise condition: new/uninstalled;
- customer-paid return shipping as the default;
- original outbound shipping as non-refundable by default with an exception for
  D'Acqua Dolce error, defective equipment, or authorized discretion; and
- acknowledgement required.

Percentages are stored as basis points so a 25% fee is represented exactly as `2500`
rather than as a floating-point percentage.

## Versioning and customer acknowledgement

Structured terms live on the same `policy_documents` version as the Refund Policy
text. When a formal quote is presented, both the approved text and the structured
terms are copied into the immutable quote policy snapshot.

The existing body SHA-256 remains unchanged in meaning. PT28 adds a separate
SHA-256 digest for structured terms, calculated from canonical JSON. Customer quote
approval continues to require acknowledgement of every attached policy snapshot, and
the audit event records both digests when structured terms are present.

This preserves evidence of the exact policy version and exact structured return terms
that accompanied the approved quote without making the current draft language legally
sufficient.

## Intentionally unresolved

PT28 does **not** choose between:

- a 60-day return window and case-by-case eligibility; or
- a 25% restocking fee and case-by-case restocking.

Those choices remain explicit configuration in a Refund Policy version.

PT28 also does not implement:

- automated refunds;
- payment-provider refund calls;
- return-merchandise authorization workflow;
- partial-return line selection;
- shipping-insurance sale, waiver, or claim handling;
- the cancellation matrix; or
- final legal policy language.

Those require subsequent business/provider/legal decisions.

## Operations behavior

Administrator/developer users can optionally attach structured return settings when
creating a Refund Policy draft. The form requires internally consistent values and
does not silently choose a return window or restocking percentage.

Employees remain read-only for policy management. Existing policy approval controls
remain unchanged.
