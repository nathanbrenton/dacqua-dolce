# PT37 — Operations hierarchy, availability demand, and account retirement

## Scope

PT37 combines three small, related Operations improvements without changing public-site typography or introducing new commerce policy:

1. strengthen the visual hierarchy of the Operations workspace;
2. expose existing customer `Notify When in Stock` demand to authorized Operations users; and
3. add a safe web-admin account disable/re-enable workflow that preserves history.

## Operations visual hierarchy

The Operations section headings and disclosure summaries are intentionally styled only beneath `.operations-shell`.

PT37:

- increases the prominence and contrast of Operations section labels;
- normalizes the scale of large internal section headings;
- strengthens collapsed disclosure titles such as `Pricing & inventory`, `User access & roles`, and `Audit log`;
- does not change global heading tokens; and
- does not change customer/public typography.

This keeps the visual fix isolated until it has been accepted in the Operations UI.

## Availability demand

The customer-facing availability foundation already existed before PT37:

- `Out of stock` presentation;
- optional estimated lead time;
- `Notify When in Stock`; and
- durable, de-duplicated stock-notification subscription records.

PT37 does not duplicate that architecture. Instead, it adds a read-only Operations view of active notification requests under `Pricing & inventory` so staff can see customer demand by product, SKU, email, and request time.

The list is evidence only. Automated availability-notification email remains uncommissioned. PT37 does not send stock email, mark subscriptions notified, or invent supplier inventory quantities.

## Account retirement

The identity model already supports `active`, `disabled`, and `locked` user states. PT37 adds a guarded administration endpoint and UI action for the existing `disabled` state.

Disabling an account:

- blocks sign-in;
- revokes currently active sessions;
- preserves the user record;
- preserves historical references;
- preserves role assignments for audit/recovery; and
- writes an `identity.account_status_changed` audit event.

Safety rules:

- an administrator cannot disable their own current account;
- the final active administrator cannot be disabled;
- developer-account status remains local-only; and
- temporary login-lockout state is not repurposed as administrative retirement.

Re-enabling a disabled account restores the `active` status but does not resurrect revoked sessions.

## Database impact

No migration is required.

PT37 reuses:

- the existing `users.status` field and `user_status` enum;
- existing `user_sessions.revoked_at` session revocation;
- the existing audit-event infrastructure; and
- the existing `stock_notification_subscriptions` table.

## Production-data boundary

Deploying PT37 does not automatically disable any production account.

After production acceptance, the obsolete Jamie application account can be disabled deliberately from `Operations -> User access & roles`. A replacement account should be created separately rather than renaming or repurposing the historical identity.
