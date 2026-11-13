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

## Content rules (customer-facing copy)

- Follow the claims boundary in `docs/PT14_CLIENT_PRODUCT_DIRECTION.md`: no
  invented facts, response times or sizing; avoid "removes"/"eliminates";
  keep the CLEAR acronym exact; "Big Blue" is not public; the equipment-only
  launch boundary must stay visible on product purchase areas and the quote flow.
- Customers see plain language. Avoid trade terms like "power" or "backwash"
  without explanation; frame things around the customer's water problem.

## UI review

- Default customer look: Lagoon Editorial theme, light appearance, Editorial
  Modern typography, background logo visible, monochrome logo. Other
  combinations are only demo options in the pop-up behind the footer logo.
- Customer pages: check desktop, wide desktop, and iPhone 15+ portrait and landscape.
- Operations: used only by the developer, on desktop. Mobile polish is low
  priority there. Operations has its own light/dark preference (default dark).

## Operations page

**Goal (current focus):** make Operations more intuitive and visually better
organised, above all for communicating with customers and fielding quotes.

**Code:**
- `frontend/src/components/operations/OperationsPage.tsx` (~6,000 lines) holds
  the header, workspace nav and most panels.
- Split-out panels in the same folder: `CommunicationsInbox.tsx` (customer
  inbox and replies), `FormalQuoteComposer.tsx` (quote drafting inside a
  request), `OrderFulfillmentControls.tsx`, `PolicyManagementPanel.tsx`,
  `LaunchDependencyEvidencePanel.tsx`, `ProductFamilyOrderPanel.tsx`.
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
| `overview` | Overview | Summary counts, readiness snapshot, observed request patterns, launch policies |
| `communications` | Inbox | Failed email deliveries (only when there are any), customer inbox |
| `requests` | Requests | Status/triage filter tabs, then a queue of requests on the left and the selected request on the right: workflow progress bar plus next step (`RequestWorkflowProgress.tsx`), Customer, Recommendation, Request, Formal quote and private notes |
| `orders` | Orders | Customer orders and fulfilment |
| `catalog` | Catalog | Pricing and inventory, availability demand, per-product accordions |
| `customers` | Customers | Accounts and address book |
| `installers` | Installers | Internal installer-candidate research |
| `staff` | Staff | User access and roles (administrator and developer only) |
| `audit` | Audit | Privileged activity history (developer only) |

**Known pain points:**
- Requests and Inbox are separate workspaces. A quote's email thread is linked
  to it in data (`related_entity_type: "quote_request"`), but you have to switch
  workspaces to see the conversation next to the request.
- A single request is still long: recommendation context and the formal
  quote builder take a lot of vertical space.
- `OperationsPage.tsx` is very large; split panels out into their own files as you touch them.

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
   add an "Open request" link to Inbox conversations.
4. Overview becomes a "Needs you" list linking straight to waiting items.

The tab order (Inbox before Requests) is unchanged. The user hasn't decided
whether Requests should come first.
