# D'Acqua Dolce — Operations UI Consistency

A pricing-policy update was correctly committed to PostgreSQL, but the same
request could return the previously loaded `product.prices` relationship from
SQLAlchemy's identity map. This made the selector visually revert until the
browser refreshed.

The operations product reload now uses
`execution_options(populate_existing=True)`, so the post-write response
replaces already-loaded ORM state with the committed pricing records.

## Current Operations layout contract

Operations is organised as workspaces in a top navigation bar
(`OPERATIONS_WORKSPACES` in `OperationsPage.tsx`). One workspace is shown at a
time, in this order:

1. Overview — priorities and readiness
2. Inbox — customer communications and failed email deliveries
3. Requests — quote requests and triage
4. Orders — fulfilment
5. Catalog — pricing and inventory
6. Customers — accounts and address book
7. Installers — internal installer-candidate research
8. Staff — user access and roles (administrator and developer only)
9. Audit — privileged activity history (developer only)

The Inbox workspace (formerly "Communications") moved to second place in
commit `181db0c`.

The tabs are grouped as Daily (Overview, Inbox, Requests, Orders), Store
(Catalog, Customers, Installers) and Admin (Staff, Audit). Requests shows the
number of new requests and Inbox the number of open customer conversations
when either is above zero. Requests and Inbox render their content directly
rather than inside a collapsed disclosure; the other workspaces keep their
disclosures and open the first one when the tab is chosen.

Pricing & Inventory product cards are collapsed by default and use a one-open-at-a-time accordion. Compact summary badges explicitly label `Lifecycle:`, `Inventory:`, and `Pricing:` so canonical product names never need lifecycle words embedded in the title.

Customer Inbox distinguishes Website, Email/Postmark, and archived/provider evidence. Website submissions are not treated as email-authentication events. Inbound/customer-supplied URLs remain non-clickable; arbitrary inbound HTML remains untrusted.

Operations keeps its own persistent light/dark appearance preference and defaults
to dark when no preference has been stored. Customer Account appearance is a
separate preference and does not overwrite the Operations preference.
