# Post-Purchase Replacement Reminder Runbook

PT22.2 provides a provider-safe reminder runner and customer-controlled calendar
export. It does not automatically commission a production timer.

## Eligibility

A replacement reminder is eligible only when all of the following are true:

- the installed-equipment record is active and linked to a catalog product;
- the customer account is active and email-verified;
- the related product relationship is active, public, and marked consumable;
- a supported `replacement_interval_days` value is recorded;
- Operations explicitly selected one reminder preference binding;
- the customer's matching communication preference is enabled;
- the derived replacement target is due on or before the runner's `--as-of`
  date; and
- that equipment/product/kind/due-date business key has not already been sent
  or deliberately suppressed.

The next replacement target uses `last_service_on` first and `installed_on`
second. No baseline or no supported interval means no scheduled reminder.

## Preview

Run from the backend environment without `--send`:

```bash
python3 -m app.cli.send_due_maintenance_reminders
```

The default mode lists eligible reminders and performs no email or database
writes.

For deterministic review:

```bash
python3 -m app.cli.send_due_maintenance_reminders --as-of 2026-10-15
```

## Send

Live sending is deliberately explicit:

```bash
python3 -m app.cli.send_due_maintenance_reminders --send
```

`--send` refuses to run unless the configured provider is Postmark and a server
token is available. Outbound messages use the existing delivery boundary and
PostgreSQL communications archive.

Do not enable a production timer until the desired customer send window has been
approved and a preview has been reviewed against production data.

## Calendar export

Signed-in customers may download `.ics` files from their Installed Systems
section for:

- a recorded `next_service_due_on` target; and
- a consumable replacement target derived from a supported replacement
  interval.

These are ordinary calendar files. No external calendar account, OAuth grant,
or background calendar write is used.
