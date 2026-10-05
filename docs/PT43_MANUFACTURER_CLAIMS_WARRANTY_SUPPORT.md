# PT43 — Manufacturer Claims Provenance + Warranty Support

## Purpose

PT43 extends the existing PT31 provenance boundary without inventing manufacturer
performance or warranty terms. It also gives customers a website support path
that lands in the already-commissioned durable Customer Inbox.

## Manufacturer-stated claims

`ApprovedProductClaim` remains the canonical record for manufacturer-sourced
performance/capacity statements. PT43 does not add a second claims table.

A claim is public only when all of the following are true:

- the record is active;
- it has an approval timestamp;
- it has a non-empty source reference;
- it has not expired.

Public presentation uses the explicit label **Manufacturer-stated** and shows the
recorded source. The application does not relabel these statements as independently
verified. Unsupported, unapproved, retired, source-less, or expired claims remain
suppressed.

Existing product specifications keep their stricter boundary: public specifications
continue to require an active/public record and a verification timestamp. Their
internal source-reference field is not newly exposed on the public API.

Operations now shows specification provenance and manufacturer-claim publication
readiness alongside the existing warranty-document provenance.

## Warranty and support request path

PT43 adds `/api/support` and a customer-facing support form for:

- warranty support;
- product support;
- general support.

Website requests are stored directly as inbound `CommunicationThread`,
`CommunicationMessage`, and `CommunicationEvent` records. They therefore enter the
existing Operations Customer Inbox instead of creating a second support database or
misusing `QuoteRequest`. Signed-in requests are linked to the authenticated customer
identity and must use that account's email address. Anonymous requests retain the
submitted normalized email address.

The structured communication event preserves support kind, contact information, and
optional product context. Operations displays this as the originating support request
while later replies continue through the existing threaded reply path.

The public support surface also exposes the already-commissioned
`support@dacquadolce.com` email channel. PT43 does not invent a public phone number;
customer-facing phone publication remains dependent on an authoritative business
number being supplied.

## Warranty boundary

PT43 does not change PT31 warranty eligibility. Manufacturer warranty documents remain
public/sale-ready only through the existing active + public + verified + SHA-256
provenance boundary, and formal-quote warranty snapshots remain immutable.

PT43 does not invent or automate warranty duration, coverage, exclusions, labor,
shipping reimbursement, claim adjudication, installer warranties, or other legal
terms.

## Database and integrations

No migration is required. PT43 reuses existing catalog claim, communication archive,
audit, authentication, Postmark inbound/reply, and warranty provenance structures.
