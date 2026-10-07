# D'Acqua Dolce — Operations UI Consistency

A pricing-policy update was correctly committed to PostgreSQL, but the same
request could return the previously loaded `product.prices` relationship from
SQLAlchemy's identity map. This made the selector visually revert until the
browser refreshed.

The operations product reload now uses
`execution_options(populate_existing=True)`, so the post-write response
replaces already-loaded ORM state with the committed pricing records.

## Current Operations layout contract

The current Operations sections are ordered as follows:

1. Customer Requests
2. Customer Orders
3. Pricing & Inventory
4. Accounts & Address Book
5. User Access & Roles
6. Customer Inbox
7. Audit Log

Pricing & Inventory product cards are collapsed by default and use a one-open-at-a-time accordion. Compact summary badges explicitly label `Lifecycle:`, `Inventory:`, and `Pricing:` so canonical product names never need lifecycle words embedded in the title.

Customer Inbox distinguishes Website, Email/Postmark, and archived/provider evidence. Website submissions are not treated as email-authentication events. Inbound/customer-supplied URLs remain non-clickable; arbitrary inbound HTML remains untrusted.

Operations keeps its own persistent light/dark appearance preference and defaults
to dark when no preference has been stored. Customer Account appearance is a
separate preference and does not overwrite the Operations preference.
