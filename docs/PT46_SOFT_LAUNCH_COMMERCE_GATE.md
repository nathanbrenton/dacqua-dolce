# PT46 — Soft Launch Readiness + Commerce Gate

## Purpose

PT46 turns launch posture into an explicit runtime control instead of leaving
commercial launch as an implication of individual integrations.

The application now distinguishes three deployment phases through
`DACQUA_LAUNCH_PHASE`:

- `prelaunch` — normal default; transactional checkout is closed.
- `soft_launch` — invited/test validation posture; transactional checkout is
  still closed.
- `public_launch` — explicitly permits checkout to proceed to the independent
  sales-area, automated-tax, payment-provider, order, and cancellation guards.

The default is deliberately `prelaunch`. A missing environment variable can
therefore never open commerce accidentally.

## Soft-launch boundary

Soft launch is not a workaround for unresolved tax, payment, legal, inventory,
or warranty work. It is a validation phase for non-payment workflows such as:

- customer accounts;
- inquiries and assisted sales;
- formal-quote preparation where existing policy guards permit it;
- warranty/support communication;
- Customer Inbox and Operations workflows;
- browser and operational acceptance testing.

PT46 does not create an invitation-list database or change public website
visibility. `soft_launch` is the commerce phase boundary; any future
invite-only access-control requirement should be implemented separately rather
than inferred from this flag.

## Checkout enforcement

`begin_hosted_checkout()` now fails closed unless the launch phase is explicitly
`public_launch`.

Selecting `public_launch` is necessary but not sufficient. Existing checkout
guards remain authoritative, including:

- approved delivery sales area;
- current authoritative automated tax evidence;
- explicitly commissioned concrete payment gateway;
- active-cancellation restrictions;
- order state and provider response validation.

PT44 still refuses sandbox tax evidence in production. PT45 still refuses an
uncommissioned production payment provider. PT46 does not weaken either
boundary.

## Operations — Commerce Launch Gate

`GET /api/operations/launch-readiness` now reports:

- current launch phase and human-readable phase label;
- whether the aggregate Commerce Launch Gate is open or closed;
- gate detail;
- current `Action required` readiness checks as blockers.

The Operations UI presents this information before the existing readiness
counts.

The aggregate display is informational. Service-level checkout guards remain
the final enforcement authority.

## Explicit public-launch transition

Moving to public launch is an operational deployment configuration change:

```text
DACQUA_LAUNCH_PHASE=public_launch
```

That transition must be intentional and reviewed together with current launch
readiness. It must not be set merely to make a test pass or to bypass an
external commissioning dependency.

## No database migration

PT46 introduces no new tables or columns. Launch phase is deployment
configuration, so rollback to a prior application release does not mutate
transaction history.
