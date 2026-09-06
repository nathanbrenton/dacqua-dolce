# D'Acqua Dolce — Local Operations Role Bootstrap

## Architecture

The repository command:

    scripts/manage_user_role.py

is intentionally a thin launcher. It does not import application modules or
modify `sys.path`.

Instead, it:

1. resolves the repository root from its own file path;
2. resolves `backend/.venv/bin/python`;
3. changes the child process working directory to `backend/`;
4. executes:

       python -m app.cli.manage_user_role

The real command implementation lives at:

    backend/app/cli/manage_user_role.py

This makes configuration loading independent of the shell's original
working directory while keeping normal Python import ordering.

## List users

    cd "$HOME/Desktop/dacqua-dolce"

    backend/.venv/bin/python \
      scripts/manage_user_role.py \
      list

The same command also works when the current directory is elsewhere if an
absolute path to the launcher is used.

## Grant developer

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

## Security boundary

No HTTP endpoint is added for role promotion.

Supported local operations roles:

- employee
- manager
- administrator
- developer

The CLI does not assign `customer`.

Role changes are limited to existing user records and emit audit events with
source `local_role_cli`.
