# PT38 — Account Roles Polish & Equipment-Only Launch Boundary

## Purpose

PT38 uses already-approved business direction to improve the Operations account-role editor and make the initial equipment-only sales boundary explicit at customer and staff decision points. It does not add installation services, installer referrals, or new installation-policy text.

## Operations account-role polish

The User Access & Roles account cards give the identity/status panel and staff-access editor enough horizontal space to remain readable. The web-managed role editor now reflects the actual UAM model instead of presenting combinable checkboxes:

- ordinary accounts have one selectable staff access level: **No staff access**, **Employee**, or **Administrator**;
- Customer access is preserved automatically and is not presented as a staff-role toggle;
- the legacy **Manager** role is shown only when an account already carries it, and must be migrated to Employee, Administrator, or No staff access rather than re-saved or newly assigned;
- **Developer** is the highest-privilege application role and remains provisioned/revoked through local administrative tooling rather than the web console;
- an administrator cannot remove their own Administrator access through the web console;
- role changes remain audited.

The single-choice radio presentation prevents the UI from implying that Employee, Manager, and Administrator are combinable permissions. Developer targets show an explicit managed-outside-the-console explanation rather than disabled role controls that look broken. These rules are scoped beneath `.operations-shell`; they do not change customer-account role or typography styles.

PT37 account disable/re-enable behavior is unchanged. Historical identities and role assignments remain preserved when an account is disabled.

## Equipment-only launch boundary

Confirmed business direction remains:

- initial launch sales are for equipment only;
- installation is arranged separately;
- D'Acqua Dolce does not currently offer installation services through the website;
- certified-installer recommendations/referrals remain a later-stage capability;
- whole-house assisted-sales requirements remain unchanged.

PT38 surfaces that boundary in the catalog, product-detail purchase area, and quote-request flow. Installation-context questions remain because installation constraints are relevant to product fit; the copy now explicitly separates those questions from an installation-service offer.

The public home-page service statement is changed from “Support beyond installation.” to “Support throughout ownership.” so it does not imply that D'Acqua Dolce performed the installation.

## Formal quote guardrail

The existing commercial-charge model retains the `installation` charge kind for historical compatibility and possible future use. For the current equipment-only launch, the Operations formal-quote composer no longer offers Installation as a new charge option. Existing historical quote data is not rewritten. No database migration is required.

## Out of scope

PT38 does not:

- create an installer network or referral workflow;
- publish installer recommendations;
- create or approve Installation Terms;
- change tax, shipping-insurance, cancellation, or payment-provider rules;
- alter the whole-house assisted-sales boundary;
- change global heading typography.

## Validation

Before commit/deploy:

1. `git diff --check` passes.
2. Frontend production build passes.
3. Operations User Access & Roles cards are checked at desktop and narrow widths.
4. Ordinary accounts show a single-choice staff access level: No staff access, Employee, or Administrator.
5. Existing Manager assignments are identified as legacy and cannot be newly assigned or re-saved unchanged.
6. Developer targets show that Developer access is managed through local administrative tooling rather than offering disabled web role controls.
7. An ordinary test account can be promoted to Employee and Administrator and returned to No staff access, subject to existing administrator self-protection.
8. Catalog, product detail, and quote request display the equipment-only boundary.
9. Product-fit forms may still ask about installation constraints without offering installation service.
10. Formal quote builder does not offer Installation as a new adjustment.
11. Customer/public typography outside the intentional PT38 callouts is visually unchanged.

## Email delivery review queue reconciliation

PT38 also makes the Operations failed-email queue represent current action required rather than every historical failure forever. Failed email-verification deliveries remain preserved in communication history, but they no longer count as an Operations alert when the related user is already verified, is disabled, or no longer exists. Other failed delivery categories remain reviewable. This is derived from current account state; no historical delivery record is rewritten or deleted.
