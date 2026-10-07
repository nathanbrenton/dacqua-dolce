# D'Acqua Dolce — Production Secret Boundary

The public Git repository may contain configuration templates and variable
names, but never populated production secrets.

Production-only values include:

- PostgreSQL runtime and migration-role passwords;
- Postmark server token;
- private Postmark inbound-routing/webhook credentials;
- AWS/S3 credentials;
- TLS private keys;
- backup encryption credentials;
- session/cryptographic secrets;
- deployment private keys;
- infrastructure API tokens.

Production secrets belong in root-controlled runtime configuration outside the
repository.

## PostgreSQL credential separation

Production uses two application-specific PostgreSQL login principals:

- `dacqua_dolce_migrator` — deploy-time DDL/Alembic and application-object
  ownership;
- `dacqua_dolce_app` — FastAPI runtime DML only.

Their passwords must be distinct.

Runtime configuration:

    /etc/dacqua-dolce/backend.env

contains only the runtime `DACQUA_DATABASE_URL` and is readable by the API
service account.

Deploy-only configuration:

    /etc/dacqua-dolce/migration.env

contains `DACQUA_MIGRATION_DATABASE_URL`, is root-owned mode `0600`, and must
never be loaded by `dacqua-dolce-api.service`.

Application users such as customer, employee, administrator, or developer never
receive either PostgreSQL credential.

## Email secret boundary

Non-secret sender identities, routing rules, DNS record names, and public DNS policies may be documented. Provider tokens, private inbound addresses, webhook Basic Auth values, Proton login/recovery secrets, and vendor session credentials may not.

Human Proton credentials belong in the approved business password manager/recovery process and are not production application secrets. The production server does not need a Proton mailbox password for the current architecture.

Postmark application secrets remain under `/etc/dacqua-dolce/`. Observability/report configuration remains separate under `/etc/dacqua-observability/`; the intended direct Postfix monitoring path must not reuse the application Postmark token.

When stored in shell environment syntax, the visible sender display name must
remain quoted:

    DACQUA_EMAIL_SENDER_NAME="D'Acqua Dolce"

The application must never print secrets during startup diagnostics or include
them in health/readiness responses.


## Production safety configuration: policy imports

`DACQUA_POLICY_IMPORT_ALLOW_LIFECYCLE_PRESERVATION` is not a secret, but it is a production safety boundary. Keep it unset/false in Production. Lifecycle-preserving policy import exists only so Local/Dev/Test can deliberately mirror Production policy state. Production policy imports remain draft-only and must pass the normal approval workflow.
