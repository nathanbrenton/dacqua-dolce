# D'Acqua Dolce — First Host Runbook

Do not run these commands on the local development Mac.

These steps are for the fresh production Debian host.

## 1. Create a workstation admin key

On the Mac, run the repository helper:

    scripts/production/create_prod_admin_ssh_key.sh

Keep the private key only on the workstation.

## 2. Create the Vultr instance

Current architecture expects a single P0 production host with Debian 13 and
approximately 4 GiB RAM.

Record:

- public IPv4/IPv6;
- chosen canonical hostname;
- Vultr recovery/console access.

Do not disable Vultr console/recovery access.

## 3. Initial root login

Use Vultr's initial access only long enough to bootstrap an administrator.

Copy the repository host-bootstrap files to a temporary root-owned directory on
the server.

## 4. Run base bootstrap

As root:

    bash bootstrap_debian13.sh

This does not harden SSH.

## 5. Create administrator

Copy only the workstation `.pub` key to the server, then run:

    bash create_admin_user.sh ADMIN_USER /path/to/admin-key.pub

Open a second terminal and verify:

    ssh -i ~/.ssh/id_ed25519_dacqua-dolce_prod-admin_macOS ADMIN_USER@HOST

Do not continue until this succeeds.

## 6. Install firewall and fail2ban

As root:

    bash install_nftables.sh /path/to/nftables.conf

    bash install_fail2ban.sh /path/to/fail2ban-dacqua.local

Keep the active SSH session open while verifying a new SSH connection.

## 7. Harden SSH

Only after administrator key login is proven:

    bash install_ssh_hardening.sh \
      ADMIN_USER \
      /path/to/sshd-dacqua-hardening.conf

Keep the original session open. Verify a new key-only login before closing it.

## 8. Configure PostgreSQL loopback boundary

Merge the supplied PostgreSQL settings into the Debian PostgreSQL 17 cluster
configuration, then reload/restart PostgreSQL and verify
`listen_addresses = '127.0.0.1'`.

Merge the supplied `pg_hba` fragment after the standard local postgres
administration entries.

## 9. Initialize database

Supply the database application password only through the process environment:

    read -s DACQUA_DB_APP_PASSWORD
    export DACQUA_DB_APP_PASSWORD

    bash init_database.sh

    unset DACQUA_DB_APP_PASSWORD

Do not store the value in shell history or in the repository.

## 10. Validate baseline

Run:

    scripts/production/verify_host_baseline.sh

Resolve every failure before application deployment.

## 11. Prepare for the first application release

The backend is installed from `backend/pyproject.toml` using
`backend/constraints-known-good.txt`.

Production installs runtime dependencies only; do not install the `dev` extra
on the production host merely to satisfy local test tooling.

If an offline production deployment is required, first prepare a wheelhouse
that matches the production Debian/Python/CPU platform. Do not reuse the local
macOS/Apple-Silicon wheelhouse as though its binary wheels were portable.

When a compatible server-side wheelhouse is available:

    export DACQUA_PYTHON_WHEELHOUSE=/path/to/python-wheels

Run the release deployment according to the deployment milestone, then unset
the variable when it is no longer needed.

See:

    docs/PYTHON_DEPENDENCY_POLICY.md
    docs/PRODUCTION_DEPLOYMENT_FOUNDATION.md

