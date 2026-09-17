# D'Acqua Dolce — First Host Runbook

Do not run these commands on the local development Mac.

These steps are for the fresh production Debian host.

## 1. Create a workstation admin key

On the Mac, run the repository helper:

    scripts/production/create_prod_admin_ssh_key.sh

Keep the private key only on the workstation.

## 2. Create the Vultr instance

Current P0 host is `dacqua-platform-prod-01`: Debian 13, 4 vCPU, 8 GiB RAM,
160 GB storage, and an 8 GiB swapfile.

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
`listen_addresses = 'localhost'`.

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

    sudo scripts/production/verify_host_baseline.sh

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



## 12. Configure the production environment

Install the repository template:

    install       -o root       -g dacqua-app       -m 0640       infra/production/backend.env.example       /etc/dacqua-dolce/backend.env

Replace every `REPLACE_*` value in the installed copy.

Never commit the populated production environment file.

Keep:

    DACQUA_EMAIL_PROVIDER=disabled

until Postmark and its DNS records are ready for live acceptance testing.

## 13. Enable the HTTP-only ACME site

After the canonical hostname resolves to the production host:

    sudo scripts/production/install_nginx_site.sh       http       YOUR_CANONICAL_HOSTNAME

This stage exposes only the Let's Encrypt ACME challenge path.
The application itself is not served over plaintext HTTP.

## 14. Issue the TLS certificate

    sudo certbot certonly       --webroot       --webroot-path /var/www/letsencrypt       --domain YOUR_CANONICAL_HOSTNAME

Do not enable the HTTPS template until certificate issuance succeeds.

## 15. Enable the HTTPS application edge

    sudo scripts/production/install_nginx_site.sh       https       YOUR_CANONICAL_HOSTNAME

The HTTPS edge:

- serves the React production build;
- proxies `/api/` and `/health` to loopback Uvicorn;
- keeps `/readiness` inaccessible publicly;
- independently blocks Swagger/OpenAPI routes;
- redirects ordinary HTTP requests to HTTPS.

## 16. Install the systemd units

Install the units under:

    infra/production/systemd/

The API remains bound only to:

    127.0.0.1:8000

The local systemd readiness check continues to use:

    http://127.0.0.1:8000/readiness

Do not route that endpoint through the public Nginx edge.

## 17. Deploy and verify

Deploy with:

    sudo scripts/production/deploy_release.sh       /path/to/release-source

From a separate machine, verify the public edge:

    scripts/production/verify_release.sh       https://YOUR_CANONICAL_HOSTNAME

Resolve every release-verification failure before enabling Postmark or
inviting production users.
