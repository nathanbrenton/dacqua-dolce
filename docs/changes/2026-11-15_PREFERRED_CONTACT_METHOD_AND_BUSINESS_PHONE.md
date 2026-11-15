# 2026-11-15 — Preferred contact method and the business phone number

## Scope

- **Preferred contact method.** The quote dialog ("Talk to an Expert" and the product quote forms), the support form and the customer profile each have a "Preferred contact method" dropdown: Email (default), Phone call or Text message. A note under it says how we'll reply; for texts it adds "Message and data rates may apply." Choosing call or text makes Phone required, checked in the browser and on the server.
  - Stored as `preferred_contact_method` on `quote_requests` and `customer_profiles`; support requests keep it in the request's event details.
  - Signed-in customers get their saved name, phone and preference filled into the quote and support forms. A form submission doesn't change the profile; only the profile page does.
  - The quote confirmation follows the choice ("…review it and text you / call you / reply by email").
  - Profile-form errors (missing or incomplete phone) now show next to Save Profile instead of at the top of the page.
- **Operations.** A request's Customer section shows the phone, a Text (`sms:`) link when text is preferred, and a "Prefers …" chip. The next-step hint names the preferred method ("The customer prefers a text message: text (951) 555-0142, then mark it contacted."). The Customers page has a "Prefers" row; Inbox shows it on the originating request. The new-request alert email adds a "Prefers:" line. There is no SMS integration: operators call or text from their own phone.
- **Business phone number.** (714) 512-0496 appears in the site footer next to support@dacquadolce.com, and in the "Prefer to reach us directly? Call … or email …" line on /support and in each product page's Warranty & support section. Both are set in `frontend/src/config/businessContact.ts`. The footer row now wraps rather than squeezing its links.

## Deployment

**Schema migration:** `a6d3f1c8b259` adds a nullable `preferred_contact_method` (`varchar(20)`, checked to `email` / `call` / `text`) to `quote_requests` and `customer_profiles`. The deploy script runs it. Existing rows stay empty ("Not set"). No catalog change: catalog reconciliation is expected to report `total_changes 0`.

Stage the exact commit from the development Mac:

    scripts/production/stage_release_rsync.sh <commit> dacqua-prod

Activate it on the production host:

    sudo /home/n8/dacqua-dolce-deploy-source/scripts/production/deploy_release.sh /home/n8/dacqua-dolce-deploy-source

After activation, Operations' launch checklist item "Public support phone" can be marked done.

## Rollback

The release active before this deployment was `20261115T002128Z` (revision `548cc6d01cf3a2842b0ea0eebdde798739d6934c`). To return to it, on the production host:

    sudo /srv/dacqua-dolce/current/scripts/production/rollback_release.sh 20261115T002128Z

The rollback leaves the two new columns in place. The previous release does not read them and runs normally; preferences saved meanwhile are kept and reappear when this release is restored.

## Validation before deployment

- `npx tsc -p tsconfig.app.json --noEmit` (frontend)
- `node --test frontend/tests/*.test.mjs` — 29 passing
- Production-mode frontend build
- `ruff check backend`; full backend regression — including 13 new contact-method tests and the migration up and down locally
- Browser checks (local): quote dialog, support form and profile at 1440x900 and iPhone width; profile save with and without a phone; signed-in prefill; a submitted test request showing the chip, Text link and tailored next step in Operations; the Customers "Prefers" row; footer at 1106 and 1440 wide and iPhone portrait/landscape; the contact line on /support and a product page

Not checked: a real alert email with the "Prefers:" line (local email is suppressed; covered by unit tests), and Operations in light appearance.

Open: confirm the SMS consent wording ("Message and data rates may apply") with whoever advises on texting rules before texting customers at volume.
