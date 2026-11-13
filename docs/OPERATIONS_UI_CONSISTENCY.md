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

Requests shows a queue on the left (name, what the customer needs, age,
status, and Human review / Lab testing tags) and the selected request on the
right. The request opens with a progress bar (`RequestWorkflowProgress.tsx`)
whose nodes are derived from the request and its formal quotes: Received,
Contacted, Quote drafted, Staff review (only when the latest quote requires
it), Presented, Customer approved (approval creates the order) and Closed.
Below it is one suggested next step with a button (Mark as contacted, Start
quote, Go to staff review, Go to quote, Close request or Reopen request) and
a secondary Close request. Unselected requests stay mounted but hidden so unsaved
quote and note drafts are kept. The Overview metrics select the first
matching request.

Each request has a Conversation section (`RequestConversation.tsx`, between
Request and Formal quote) showing its customer email thread and a reply box.
The thread is the most recent Inbox-kind thread linked to the request
(`GET /api/operations/quotes/{id}/conversation`); System threads such as
staff alerts are skipped. With no thread yet, the reply box reads "Email the
customer", addressed to the request email from a sales sender, and the first
reply creates the linked thread (`POST …/conversation/reply`), so opening a
request never leaves an empty thread in the Inbox. A reply that isn't a
failed delivery moves a New request to Contacted. Long threads scroll inside
the section, starting at the latest email. "Open in Inbox" jumps to the
thread; Inbox conversations linked to a request show "Open request →" back.
The message list and reply form are shared with the Inbox
(`ConversationThread.tsx`).

Pricing & Inventory product cards are collapsed by default and use a one-open-at-a-time accordion. Compact summary badges explicitly label `Lifecycle:`, `Inventory:`, and `Pricing:` so canonical product names never need lifecycle words embedded in the title.

Customer Inbox distinguishes Website, Email/Postmark, and archived/provider evidence. Website submissions are not treated as email-authentication events. Inbound/customer-supplied URLs remain non-clickable; arbitrary inbound HTML remains untrusted.

Operations keeps its own persistent light/dark appearance preference and defaults
to dark when no preference has been stored. Customer Account appearance is a
separate preference and does not overwrite the Operations preference.
