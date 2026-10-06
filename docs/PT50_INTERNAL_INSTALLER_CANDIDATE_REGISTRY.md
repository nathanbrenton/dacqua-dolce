# PT50 — Internal Installer Candidate Registry

## Purpose

PT50 creates an internal-only research registry for possible future installer
candidates without creating or implying a customer-facing referral program.

## Boundaries

- The registry is available only inside authenticated Operations.
- Operations roles may read candidate records.
- Administrator and Developer roles may create or update candidate records.
- There is no public API, public directory, referral workflow, or publication flag.
- A record does **not** mean that D’Acqua Dolce has approved, recommended,
  vetted, licensed, insured, partnered with, or otherwise endorsed the candidate.
- Candidate records are retired with the `Inactive` status rather than deleted.
- PT50 does not resolve installer-program legal requirements.

## Candidate lifecycle

The internal status values are:

- `Researching`
- `Contacted`
- `Review Pending`
- `Inactive`

These are research/workflow states only. None represents public approval.

## Stored information

A candidate record can hold a business name, contact name, email, phone,
website text, service-area notes, source/provenance reference, internal notes,
status, staff provenance, and timestamps. Service areas remain free-form in
PT50 so the application does not invent a geographic installer-program policy.

## Auditability

Create and update operations record audit events. Audit metadata records the
business name/status or changed field names, but does not copy candidate contact
details or internal notes into the audit log.

## Deferred

The following remain deferred until legal/client decisions exist:

- public installer directory
- customer referrals
- approval/vetting labels
- licensing or insurance verification claims
- referral compensation
- geographic publication policy
- installer agreements or partnership claims
