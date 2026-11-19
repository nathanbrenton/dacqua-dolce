# 2026-11-19 — Mobile autocorrect off on every text field

## Scope

- **Mobile autocorrect is off on every text field (behaviour change).** iPhone autocorrect was changing names and street addresses as customers typed them.
  - New helper `frontend/src/components/forms/textEntry.ts` with two settings:
    - `exactEntryProps` (`autoCorrect="off"`, `spellCheck={false}`): names, addresses, ZIPs, emails, phones, codes, IDs, numbers, URLs and search boxes.
    - `proseEntryProps` (`autoCorrect="off"` only): message and notes boxes, which keep the spelling underline.
  - Every text `<input>` and `<textarea>` spreads one of the two: 78 fields in 29 files, covering the customer site (quote dialog, support form, sign-in, forgot password, account profile and addresses, product notify-me, recommendation form) and Operations. The shared `UsPhoneInput`, `PasswordInput` and `MoneyInput` use `exactEntryProps`.
  - `autoCapitalize="none"` was added only on fields that hold an email address or URL as plain text: Operations reply recipients and the Installers website fields.
  - Checkboxes, radio buttons, date pickers and file pickers are unchanged.
- **New test** `frontend/tests/text-entry-autocorrect.test.mjs` fails if any text field in `frontend/src` lacks one of the two settings.

Commits since the active release: this one only.

## Deployment

Frontend only. No schema migration and no catalog change: catalog reconciliation is expected to report `total_changes 0`.

Stage the exact commit from the development Mac:

    scripts/production/stage_release_rsync.sh <commit> dacqua-prod

Activate it on the production host:

    sudo /home/n8/dacqua-dolce-deploy-source/scripts/production/deploy_release.sh /home/n8/dacqua-dolce-deploy-source

## Rollback

The release active before this deployment was `20261119T002106Z` (revision `e0e964636fe44f86b1a4d35ef0f7f61964d4deeb`). To return to it, on the production host:

    sudo /srv/dacqua-dolce/current/scripts/production/rollback_release.sh 20261119T002106Z

After a rollback, iPhone autocorrect again changes text in the site's fields.

## Validation before deployment

- `npx tsc -p tsconfig.app.json --noEmit` (frontend)
- `node --test frontend/tests/*.test.mjs`: 30 passing, including the new test; it was also checked to fail when one field's setting is removed
- Production-mode frontend build
- Browser check (local, `/support` at 375×812 and 812×375): all 12 fields on the page (sign-in, quote dialog, support form) render `autocorrect="off"`; the message boxes keep spell-check; layout unchanged, no horizontal scroll.

**Not yet checked:** the iPhone keyboard itself (the local browser ignores this attribute, as only Safari uses it). After activating, type a name and street address into the quote dialog or support form on an iPhone, in portrait and landscape.
