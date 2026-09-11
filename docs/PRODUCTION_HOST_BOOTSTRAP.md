# D'Acqua Dolce — Production Host Bootstrap

## Target

P0 assumes one appropriately sized Vultr production instance, with roughly
4 GiB RAM as the current planning baseline because the initial host will carry:

- Nginx;
- FastAPI/Uvicorn;
- native PostgreSQL 17;
- backup tooling;
- P0 observability components.

This repository milestone prepares the host but does not create the Vultr
instance itself.

## Accounts and keys

Use separate identities for separate purposes.

### Production administrator login

A workstation-generated SSH key is used for human administrator login.

Suggested local path:

    ~/.ssh/id_ed25519_dacqua-dolce_prod-admin_macOS

Only its public key is installed on the server.

### Application service account

The host contains:

    dacqua

as a system service account with `/usr/sbin/nologin`.

The application must not run as root.

### Future server-to-GitHub deployment key

If the server later needs direct GitHub repository access, create a separate
server deployment key such as:

    dacqua-dolce-prod_deploy_ed25519

Do not copy the workstation administrator private key to the server, and do not
reuse the local GitHub deploy private key.

## Staged SSH hardening

SSH lockdown is deliberately separate from initial bootstrap.

Sequence:

1. create an administrator account;
2. install its public SSH key;
3. open a second terminal and prove key login works;
4. only then install the SSH hardening drop-in;
5. keep the original session open while testing the hardened login.

The hardening installer refuses to continue if the selected administrator does
not already have a non-empty `authorized_keys`.

## Firewall

The P0 nftables policy is default-deny inbound and permits:

- loopback;
- established/related connections;
- ICMP/ICMPv6;
- TCP 22;
- TCP 80;
- TCP 443.

PostgreSQL 5432, Uvicorn 8000, Grafana, Prometheus, exporters, Loki, and other
internal observability listeners are not publicly allowed by this baseline.

As observability services are added, keep them loopback/private unless a
specific authenticated network path requires otherwise.

## fail2ban

The included jail enables protection for `sshd`.

This supplements SSH keys and firewall policy; it is not a substitute for
either.

## PostgreSQL

PostgreSQL 17 is native on the production host.

Network policy:

    listen_addresses = '127.0.0.1'

Application role:

    dacqua_dolce_app

Database:

    dacqua_dolce

The application role is:

- LOGIN;
- NOSUPERUSER;
- NOCREATEDB;
- NOCREATEROLE;
- NOREPLICATION.

The initialization script reads the password from:

    DACQUA_DB_APP_PASSWORD

It does not place a password in the repository.

## What is intentionally deferred

This milestone does not yet configure:

- DNS;
- Let's Encrypt certificate issuance;
- populated `/etc/dacqua-dolce/backend.env`;
- Postmark production secrets;
- pgBackRest/S3;
- Monit;
- Prometheus/exporters;
- Alertmanager;
- Alloy/Loki;
- Grafana;
- Better Stack;
- deployment of the first application release.

Those are subsequent production milestones.
