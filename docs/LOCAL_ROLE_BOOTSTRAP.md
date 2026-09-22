# D'Acqua Dolce — Account Role Administration and CLI Bootstrap

## Role model

Registered accounts receive the `customer` role through the normal application flow.

Operations roles are:

- `employee`
- `manager`
- `administrator`
- `developer`

Operations access is enforced by FastAPI, not only by frontend visibility.

Administration access is limited to `administrator` and `developer` accounts.

## Web-managed roles

The authenticated Operations console includes **User Access & Roles** administration for:

- `employee`
- `manager`
- `administrator`

The web administration API deliberately does not manage `developer`.

Safety rules include:

- preserve the account's `customer` role when changing operations roles;
- an administrator cannot remove their own administrator role;
- the final active administrator role cannot be removed;
- any account carrying `developer` is rejected by the web role editor and must be managed through the local CLI;
- successful changes emit an audit event with source `web_administration`.

## Local CLI architecture

The repository command:

    scripts/manage_user_role.py

is intentionally a thin launcher. It does not import application modules or modify `sys.path`.

Instead, it:

1. resolves the repository root from its own file path;
2. resolves `backend/.venv/bin/python`;
3. changes the child process working directory to `backend/`;
4. executes:

       python3 -m app.cli.manage_user_role

The real command implementation lives at:

    backend/app/cli/manage_user_role.py

This makes configuration loading independent of the shell's original working directory while keeping normal Python import ordering.

## List users

    cd "$HOME/Desktop/dacqua-dolce"

    backend/.venv/bin/python \
      scripts/manage_user_role.py \
      list

The same command also works when the current directory is elsewhere if an absolute path to the launcher is used.

## Grant developer

Use the CLI for `developer` because that role is intentionally outside web administration:

    backend/.venv/bin/python \
      scripts/manage_user_role.py \
      add \
      --email "existing-user@example.com" \
      --role developer

## Revoke developer

    backend/.venv/bin/python \
      scripts/manage_user_role.py \
      remove \
      --email "existing-user@example.com" \
      --role developer

The CLI can also manage the ordinary operations roles when local recovery/bootstrap requires it. It does not assign `customer`.

## Production bootstrap boundary

At least one verified production account must be promoted through the local CLI before web administration can bootstrap itself. After an administrator exists, ordinary employee/manager/administrator changes should normally use the audited web interface.

Role changes remain limited to existing user records. Do not create shared staff credentials or embed privileged role assignments in frontend code.
