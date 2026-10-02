# PT31 — Warranty & Manufacturer Terms Infrastructure

## Purpose

PT31 establishes a provenance-safe warranty-document chain without inventing manufacturer coverage terms.

D’Acqua Dolce remains the customer’s primary warranty contact at launch. Product-specific warranty promises must come from verified manufacturer documentation.

## Product warranty documents

`ProductDocument` remains the canonical product-document record. Warranty documents now carry optional source/reference and verification provenance:

- `source_reference`
- `verified_at`
- `verified_by_user_id`
- existing version and SHA-256 checksum fields

A warranty document is sale-ready only when it is active, public, verified, and has a 64-character SHA-256 checksum. Other document types retain their existing publication behavior.

## Formal quote snapshots

When a formal quote is presented, every sale-ready warranty document for its catalog products is copied into an immutable `formal_quote_warranty_snapshots` row containing the product, manufacturer, title, version, path, content type, checksum, source reference, and verification timestamp as they existed at presentation.

The snapshot is independent from the mutable catalog record. Later replacement or retirement of a warranty document does not rewrite a previously presented quote.

PT31 does not block quote presentation when manufacturer documentation is not yet available. The existing approved D’Acqua Dolce Warranty policy remains a required quote policy; manufacturer documents are additive product-specific evidence.

## Customer and Operations visibility

- Public product warranty documents are exposed only after verification.
- Customer equipment hides unverified warranty documents while leaving other public product documents unchanged.
- Presented quotes show immutable manufacturer warranty snapshots when available.
- Operations catalog governance shows recorded warranty documents and their verification/publication state.
- D’Acqua Dolce is identified as the primary warranty-support contact in the customer quote view when manufacturer snapshots are attached.

## Deferred

PT31 intentionally does not invent or automate:

- warranty duration;
- covered components;
- exclusions;
- labor or shipping reimbursement;
- full vs. limited warranty designation;
- manufacturer claim adjudication;
- installer warranties;
- warranty document upload/storage transport.

Those require authoritative manufacturer documents and, where appropriate, legal review.
