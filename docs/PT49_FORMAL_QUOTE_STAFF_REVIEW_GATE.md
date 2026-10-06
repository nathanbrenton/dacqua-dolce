# PT49 — Formal Quote Staff Review Gate

## Purpose

PT49 makes the client's assisted-sales decision enforceable at the formal-quote
presentation boundary without inventing a dollar threshold or a second quote workflow.

## Rules

- Every new formal-quote revision containing a product whose canonical catalog record
  has `assisted_sale_required = true` automatically requires staff review/customer
  contact before it can be presented.
- Staff may explicitly flag any other unusually large or complex quote revision for
  the same review gate.
- PT49 deliberately does not infer "large" from a dollar amount. No price threshold is
  encoded.
- Review is revision-specific. A new revision gets its own review requirement and
  evidence; review of an older revision does not silently carry forward.
- Required review must be explicitly completed by authenticated Operations staff before
  the draft-to-presented transition.
- Review completion records the staff actor, timestamp, reason codes, and audit event.
- Historical formal quotes are migrated with no review requirement so PT49 does not
  retroactively change already-created quote evidence.

## Reason codes

- `assisted_sale_product` — at least one quote line is an assisted-sale product.
- `staff_flagged_complex` — staff explicitly marked the quote as unusually large or
  complex.

These are operational reason codes, not customer-facing legal classifications.

## Existing boundaries preserved

PT49 does not:

- change the 30-day formal quote validity period;
- enable live checkout;
- change tax, payment, warranty, return, or cancellation policy;
- implement an Affinity24 adapter;
- create a monetary definition of a large order;
- require a particular customer contact method.

The existing formal quote draft/presented/approved/superseded lifecycle remains
authoritative. PT49 only adds an auditable prerequisite to presentation when review is
required.
