# D'Acqua Dolce — Account Role Administration and CLI Bootstrap

## Role model

Application identities and PostgreSQL service principals are separate security
domains.

Application roles are:

- `customer`
- `employee`
- `manager` — legacy/deprecated; retained for schema compatibility and existing
  assignments only
- `administrator`
- `developer`

Customers, employees, administrators, and developers never receive direct
PostgreSQL credentials. FastAPI reaches PostgreSQL through the constrained
`dacqua_dolce_app` runtime principal.

Canonical development/test staff fixtures use one effective staff role rather
than stacked staff/customer roles:

- `developer@dacquadolce.test` -> `developer`
- `admin@dacquadolce.test` -> `administrator`
- `employee@dacquadolce.test` -> `employee`
- `customer@dacquadolce.test` -> `customer`
- `payment-test-customer@dacquadolce.test` -> `customer`

The payment-test account remains an ordinary customer so sandbox payment work
exercises realistic customer authorization. There is no persisted guest role or
canonical guest account.

These addresses are fixture labels, not a production naming scheme. Do not
create `developer@dacquadolce.com`, `admin@dacquadolce.com`,
`employee@dacquadolce.com`, or `payment-test-customer@dacquadolce.com` merely
to mirror the development/test accounts. Production uses real individual
identities and assigns application roles to those identities.

Bootstrap passwords are supplied outside Git through
`~/.dacqua-dolce/dev-bootstrap.env`. Do not commit or print reusable plaintext
passwords.

## Capability model

Backend authorization is authoritative. Frontend visibility mirrors these
boundaries only for UX.

| Capability | Employee | Administrator | Developer |
| --- | --- | --- | --- |
| Customer Inbox / customer communications | yes | yes | yes |
| Customer requests/orders operations | yes | yes | yes |
| Pricing & Inventory read | yes | yes | yes |
| Pricing & Inventory write | no | yes | yes |
| User Access & Roles administration | no | yes | yes |
| Audit Log read | no | no | yes |

Legacy `manager` assignments remain accepted for ordinary Operations access
during transition, but the role cannot be newly assigned. Do not use `manager`
for new fixtures or staff provisioning.

Privileged accounts remain subject to the application's MFA policy.

## Web-managed roles

The authenticated Operations console may manage ordinary staff access but must
not become a path to provision or revoke `developer`.

The web role editor:

- allows at most one web-managed staff role on an account;
- does not newly assign the legacy `manager` role;
- refuses to edit an account carrying `developer`;
- prevents an administrator from removing their own administrator role;
- prevents removal of the final active administrator;
- records successful changes as audited `web_administration` activity.

`developer` provisioning and replacement is intentionally out-of-band through
the CLI.

## Role-management CLI architecture

The repository command:

    scripts/manage_user_role.py

is a thin launcher. It resolves the repository root and backend virtual
environment, changes the child working directory to `backend/`, and executes:

    python3 -m app.cli.manage_user_role

The implementation lives at:

    backend/app/cli/manage_user_role.py

The commands operate only on existing application-user rows. They do not create
users, issue PostgreSQL credentials, or manipulate PostgreSQL service
principals.

## List users and roles

From the repository root:

    backend/.venv/bin/python3 \
      scripts/manage_user_role.py \
      list

## Grant a staff role

Use `add` when intentionally adding an additional staff role to an existing
account. New `manager` assignments are rejected.

    backend/.venv/bin/python3 \
      scripts/manage_user_role.py \
      add \
      --email "existing-user@example.com" \
      --role developer

The CLI deliberately does not assign `customer`; normal customer application
flows own that role.

## Revoke a staff role

    backend/.venv/bin/python3 \
      scripts/manage_user_role.py \
      remove \
      --email "existing-user@example.com" \
      --role developer

Removing the final active developer is refused.

## Replace all roles with exactly one staff role

For deliberate identity migration, use:

    backend/.venv/bin/python3 \
      scripts/manage_user_role.py \
      set-staff-role \
      --email "existing-user@example.com" \
      --role developer \
      --confirm-replace-all-roles

`set-staff-role` is intentionally stronger than `add`/`remove`:

- it requires `--confirm-replace-all-roles`;
- it removes every existing application role on the target, including
  `customer`;
- it replaces them with exactly one of `employee`, `administrator`, or
  `developer`;
- it rejects `manager` as a new target;
- it protects the final active developer;
- it records an `identity.roles_replaced` audit event.

Use it only after confirming that the target identity is intended to be a
staff-only account.

## Development/test bootstrap

Canonical dev/test fixtures are created with:

    scripts/bootstrap_dev_users.py

The wrapper invokes the backend CLI implementation. The workflow is
development/test-only and must never be used to reset production identities.

Development/test account bootstrap is repeatable and should be paired with the
guarded local database rebuild when a clean environment is required.

The password file provides:

- `DACQUA_BOOTSTRAP_DEVELOPER_PASSWORD`
- `DACQUA_BOOTSTRAP_ADMIN_PASSWORD`
- `DACQUA_BOOTSTRAP_EMPLOYEE_PASSWORD`
- `DACQUA_BOOTSTRAP_CUSTOMER_PASSWORD`
- `DACQUA_BOOTSTRAP_PAYMENT_TEST_PASSWORD`

Load it into the current shell without printing it, then run the bootstrap:

    set -a
    . "$HOME/.dacqua-dolce/dev-bootstrap.env"
    set +a

    backend/.venv/bin/python3 \
      scripts/bootstrap_dev_users.py

The bootstrap refuses to run when `DACQUA_ENVIRONMENT` resolves to production
and does not print the passwords.

Production uses preservation/migration in place instead.

## Production boundary

Production identity administration is a preservation exercise:

- audit existing users and role assignments before mutation;
- preserve legitimate customer accounts and related business data;
- preserve MFA, credential, communication, and audit history;
- use the role CLI for developer provisioning/recovery or deliberate
  `set-staff-role` migrations;
- do not run the canonical dev fixture bootstrap in production;
- do not run the destructive local database rebuild in production;
- do not use ad-hoc SQL to delete/recreate identities when an audited in-place
  role migration is sufficient.

Application roles remain separate from PostgreSQL principals throughout.
