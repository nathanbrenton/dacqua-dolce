# D'Acqua Dolce — notes for Claude

D'Acqua Dolce is an early-stage premium water-systems business (softeners,
carbon filtration, drinking-water systems). This repo is its website: a public
catalog and quote flow for customers, plus an internal **Operations** console.
It is developed locally and deployed to one production host.

## Layout

- `frontend/` — React 19 + Vite + TypeScript. No router: paths are switched in
  `src/App.tsx`. All styling lives in one large `src/styles.css`, organised as
  dated/labelled sections appended over time (`/* PT45-D — … */`). Add new
  rules as a new labelled section at the end rather than editing old ones.
  Themes are driven by `data-theme` / `data-appearance` / `data-typography`
  on `:root`.
- `backend/` — FastAPI + SQLAlchemy + Alembic, PostgreSQL 17.
- `docs/` — feature and policy records (`PT##_*.md`), plus `docs/changes/`
  with one note per shipped change, including its deploy and rollback commands.
- `scripts/production/` — staging, deploy and rollback scripts.
- Sibling folders in `~/Desktop/dacqua-dolce_ALL/`: `dacqua-dolce-chatbot`
  (separate git repo), `dacqua-dolce-business` (business documents, **not** under
  git, so edits there cannot be undone), `dacqua-dolce_build-assets` (media
  sources). Scripts find these relative to their own location; don't hardcode
  home-directory paths.

## Notes for local agents (OpenCode + LM Studio)

A local model (Qwen3.8-27B in OpenCode, set up per `../README.txt`) also works
in this repo, with a 64K-token window. It reads this file at the start of
every session. To work within that window:

- **Never read these whole; search them, then read only the lines you need**
  (e.g. 150–300 lines around a match). Approximate size in tokens:
  `frontend/src/styles.css` ~50K, `backend/app/api/operations.py` ~43K,
  `frontend/src/components/catalog/ProductDetailPage.tsx` ~15K.
- Most other frontend files are small enough to read whole (under ~10K
  tokens). Operations and the customer account page are split into one
  file per tab or section (see "Operations page" and "Customer account
  page" below): open the file for the part you're changing, not the page.
- New CSS goes in a new labelled section at the end of `styles.css`; append
  it rather than reading the file.
- Start each new session with `/catchup` (recent commits and release notes),
  and start a fresh session after other agents have changed the code: an old
  session still remembers the files as they were.
- Work in small steps, run the checks under "Checks" after each change, and
  never commit, push or stage a release: that needs the user's go-ahead.

## Running locally

- Postgres: Docker container `dacqua-dolce-postgres` on `127.0.0.1:15432`.
  Docker Desktop must be running first.
- Backend: from `backend/`, `.venv/bin/uvicorn --reload --host 127.0.0.1 --port 8000 app.main:app`
- Frontend: from `frontend/`, `npm run dev` → `http://127.0.0.1:15173/` (proxies `/api`).
- Start servers with background Bash. The Browser pane's `preview_start` hangs
  on this folder (`getcwd: Operation not permitted`); open the URL in the
  Browser pane with `navigate` instead.
- The Operations page needs a signed-in operations role. Local dev users come
  from `backend/app/cli/bootstrap_dev_users.py` (see `docs/LOCAL_ROLE_BOOTSTRAP.md`).

## Checks

- Frontend typecheck: `npx tsc -p tsconfig.app.json --noEmit` (from
  `frontend/`). **`npm run typecheck` checks nothing**: the root
  `tsconfig.json` has `"files": []` and only references sub-projects.
- Frontend tests: `node --test tests/*.test.mjs` (from
  `frontend/`; these tests pin exact strings and element order on product
  pages, so copy or layout edits there can break them); production build with
  `VITE_APP_ENVIRONMENT=production VITE_DEVELOPER_MODE=false npx vite build`.
- Backend lint: `ruff check backend`.
- Full backend suite: `LC_ALL=en_US.UTF-8 bash scripts/pt35/run_backend_regression.sh`
  from the repo root (needs `LC_ALL` or Postgres refuses to start).

## Shipping

- Work is committed straight to `main` and pushed to GitHub, but only when the
  user says so. Ask before committing, pushing or staging a release.
- Release: `scripts/production/stage_release_rsync.sh <commit> dacqua-prod`
  stages it (Claude can run this). Activation runs on the host with `sudo` and
  needs the user's password, so **the user activates** — give them the exact
  command the stage script prints.
- Every release note in `docs/changes/` records the rollback command
  (`sudo /srv/dacqua-dolce/current/scripts/production/rollback_release.sh <timestamp>`;
  it does not touch the database).
- `deploy_release.sh` ends by printing that rollback command, filled in with
  the release that was active before, so the user has it at hand.

## Content rules (customer-facing copy)

- Follow the claims boundary in `docs/PT14_CLIENT_PRODUCT_DIRECTION.md`: no
  invented facts, response times or sizing; avoid "removes"/"eliminates";
  keep the CLEAR acronym exact; "Big Blue" is not public; the equipment-only
  launch boundary must stay visible on product purchase areas and the quote flow.
- Public phone and support email live in `frontend/src/config/businessContact.ts`;
  they appear in the footer and in the support areas ("Prefer to reach us
  directly?" on /support and product pages). Change them there only.
- Customers see plain language. Avoid trade terms like "power" or "backwash"
  without explanation; frame things around the customer's water problem.

## Customer account page

`frontend/src/components/account/AccountPage.tsx` (~430 lines) handles
sign-in states, loads the account data and holds the shared alert, success
toast and one busy flag (a save anywhere disables the other save buttons).
`SecurityPanel.tsx` and `AppearancePanel.tsx` are shown to every account,
staff included. Customer panels are in `account/sections/`: `ProfileSection`,
`AddressesSection`, `CommunicationPreferencesSection`, `EquipmentSection`,
`MaintenanceChecksSection`, `ConsultationHistorySection`,
`FormalQuotesSection` (approval prepares an order, so orders are refetched),
`CartSection`, `OrdersSection`. Shared formatting in `accountFormat.ts`;
shared props in `accountShared.ts`. API calls: `frontend/src/api/account.ts`,
`cart.ts`, `orders.ts`.

## UI review

- Default customer look: Lagoon Editorial theme, light appearance, Editorial
  Modern typography, background logo visible, Metallic / Aqua logo (no "Filtration Systems"
  subtitle; header and footer always show the same artwork). Other
  combinations are only demo options in the pop-up behind the footer logo.
- Customer pages: check desktop, wide desktop, and iPhone 15+ portrait and landscape.
- Operations: used only by the developer, on desktop. Mobile polish is low
  priority there. Operations has its own light/dark preference (default dark).

## Operations page

**Goal (current focus):** make Operations more intuitive and visually better
organised, above all for communicating with customers and fielding quotes.

**Code** (all under `frontend/src/components/operations/`; every workspace
file starts with a comment naming its API calls, backend routes and styles):
- `OperationsPage.tsx` (~800 lines): header, workspace nav, loading the data
  several workspaces share (requests, orders, customers, products,
  communications, summary), and the shortcuts that jump between workspaces.
  Each tab is a component it renders.
- `workspaces/` — one file per tab: `OverviewWorkspace`, `InboxWorkspace`,
  `RequestsWorkspace`, `OrdersWorkspace`, `CatalogWorkspace`,
  `CustomersWorkspace`, `InstallersWorkspace`, `StaffWorkspace`,
  `AuditWorkspace`.
- `requests/` — `RequestDetail.tsx` (one request in the detail pane) and
  `requestLabels.ts` (statuses, filters, recommendation labels).
- `catalog/` — `CatalogProductCard.tsx` (one product) and its editors:
  `ProductRelationships`, `ProductPricingFields`, `ProductTaxFields`,
  `ProductAvailabilityFields`; shared modes and draft builders in
  `catalogConstants.ts`. Each editor keeps its own product's draft.
- Shared pieces: `CommunicationsInbox.tsx` (customer inbox),
  `ConversationThread.tsx` (message list and reply form shared by the Inbox
  and requests), `RequestConversation.tsx`, `RequestWorkflowProgress.tsx`,
  `FormalQuoteComposer.tsx` (quote drafting inside a request),
  `OrderFulfillmentControls.tsx`, `NeedsYouList.tsx`,
  `PolicyManagementPanel.tsx`, `LaunchDependencyEvidencePanel.tsx`,
  `ProductFamilyOrderPanel.tsx`, `CopyEmailButton.tsx`, `MoneyInput.tsx`;
  helpers in `operationsMoney.ts`, `operationsNextSteps.ts`,
  `operationsShared.ts` (save-state type, `onMessage`/`onError` props).
- After a save, show the server's reply straight away (replace the item in
  state with what the API returns), and call the page's
  `refreshOverviewData` when the change can move Overview's counts or
  readiness. Backend routes that reload a row after changing its child rows
  need `populate_existing=True` (the session keeps objects across commits),
  as in `load_product_for_operations` and `load_user_with_roles`.
- API calls: `frontend/src/api/operations.ts`; backend routes in `backend/app/api/operations.py`.
- Styles: the many "Operations …" sections of `src/styles.css`; the workspace
  nav is under `/* PT45-D — Workspace navigation … */`.

**Structure today:** a top nav of workspaces (`OPERATIONS_WORKSPACES`),
grouped as Daily / Store / Admin (`OPERATIONS_WORKSPACE_GROUPS`). Requests and
Inbox show a count when work is waiting (new requests; open Inbox
conversations). One workspace panel is visible at a time. Requests and Inbox
show their content directly; the other panels still keep their sections in
collapsible `<details>` disclosures.

| Workspace | Label shown | What's in it |
|---|---|---|
| `overview` | Overview | "Needs you" work list (`NeedsYouList.tsx`), summary counts, readiness snapshot, observed request patterns, launch policies |
| `communications` | Inbox | Failed email deliveries (only when there are any), customer inbox |
| `requests` | Requests | Status/triage filter tabs, then a queue of requests on the left and the selected request on the right: workflow progress bar plus next step (`RequestWorkflowProgress.tsx`), Customer, Recommendation, Request, Conversation (`RequestConversation.tsx`), Formal quote and private notes |
| `orders` | Orders | Customer orders and fulfilment |
| `catalog` | Catalog | Pricing and inventory, availability demand, per-product accordions |
| `customers` | Customers | Accounts and address book |
| `installers` | Installers | Internal installer-candidate research |
| `staff` | Staff | User access and roles (administrator and developer only) |
| `audit` | Audit | Privileged activity history (developer only) |

**New-request email alerts:** `DACQUA_EMAIL_OPERATOR_TO` (in
`/etc/dacqua-dolce/backend.env` on production) takes one address or a
comma-separated list. Each inbox gets its own copy (category
`quote_operator_notification`, filed under Inbox > System); blank turns
alerts off. The alert is deliberately short: subject "New product inquiry —
<customer name>" (or expert / recommendation inquiry; the sender already says
D'Acqua Dolce), then name, email, phone, preferred contact method, product
family, and under "Message:" only the customer's own words (the product
configuration summary is stripped by `customer_message_text`). No footer line.
Full details stay in Operations. Apple Mail on iPhone may file the
alerts under Promotions; each phone fixes that once with ⋯ → Categorize
Sender → Primary.

**Preferred contact method:** the quote dialog, support form and customer
profile each have a "Preferred contact method" dropdown (Email / Phone call /
Text message; `utils/contactMethod.ts` mirrors `backend/app/core/contact_method.py`).
Call or text requires a phone, checked on both sides. It is stored on
`quote_requests` and `customer_profiles` (`preferred_contact_method`; support
requests keep it in the event details). Signed-in customers get their saved
name, phone and preference prefilled; a form submission doesn't change the
profile. Operations shows it as a chip and an `sms:` link on the request, on
the Customers page and in the Inbox, puts a "Prefers:" line in the alert email,
and words the request's next step to match it. There is no SMS integration:
operators call or text from their own phone.

**Failed email deliveries:** Inbox > Delivery issues lists failed sends that
still need a look. "Mark reviewed" (one or all) sets
`email_deliveries.reviewed_at` / `reviewed_by_user_id`, writes a
`communications.delivery_reviewed` audit event, and removes them from
Delivery issues, the summary count and Needs you.

**Known pain points:**
- The Inbox thread list only loads the 200 most recent threads, and System
  mail (alerts, verification) fills most of that locally. A request's
  Conversation section loads its own thread, so it isn't affected.
- A single request is still long: recommendation context and the formal
  quote builder take a lot of vertical space.

**Redesign plan (agreed 2026-11-12):**
1. Quick wins: grouped tabs, waiting counts, Requests and Inbox open by
   default. **Done.**
2. Requests as a list plus a detail pane (like the Inbox), with a workflow
   progress bar and one next step. **Done.** The bar's steps are worked out
   from the request and its formal quotes: Received → Contacted → Quote
   drafted → Staff review (only when required) → Presented → Customer
   approved (this creates the order) → Closed. Presenting needs a customer
   account under the request email plus delivery and billing addresses.
   Every request stays mounted (unselected ones are `hidden`) so quote and
   note drafts survive switching; Overview shortcuts select the first match.
3. Show the linked email conversation, with a reply box, inside the request;
   add an "Open request" link to Inbox conversations. **Done.** The request
   loads its own thread (`/api/operations/quotes/{id}/conversation`, skipping
   System threads); with none yet, the first reply creates one linked to the
   request. Replying to a New request marks it Contacted. "Open in Inbox" and
   "Open request →" link the two workspaces both ways.
4. Overview becomes a "Needs you" list linking straight to waiting items.
   **Done.** It lists, oldest first: requests whose next step is yours,
   open Inbox conversations where the customer wrote last, paid orders
   needing action, and failed email deliveries (one row). Each row opens
   that item. Items waiting on the customer, supplier or carrier sit in a
   collapsed "Waiting on someone else" group. The request and order rules
   live in `operationsNextSteps.ts` (plain TS, tested by
   `tests/operations-next-steps.test.mjs`) and also drive the progress bar.
   It replaced the single "Next action" card.

The tab order (Inbox before Requests) is unchanged. The user hasn't decided
whether Requests should come first.
