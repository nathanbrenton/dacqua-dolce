# D'Acqua Dolce

**Water, Elevated.**

D'Acqua Dolce is a mobile-first water-filtration commerce and customer-lifecycle platform.

## Application stack

### Frontend
- TypeScript
- React 19
- Vite

### Backend
- Python
- FastAPI
- SQLAlchemy 2
- Alembic
- PostgreSQL 17

### Production infrastructure
- Vultr / Debian 13
- Nginx + Let's Encrypt/Certbot
- PostgreSQL 17 as a native system service
- Prometheus / Alertmanager / Grafana / Loki / Alloy / Monit
- Better Stack external monitoring
- validated local PostgreSQL backup + full restore validation
- restic encryption layer prepared; AWS S3 off-host repository pending
- Postmark HTTPS API commissioned for application transactional/customer mail
- Cloudflare Email Routing commissioned for public `support@dacquadolce.com` inbound mail
- PostgreSQL communications archive + Operations Customer Inbox commissioned
- direct Postfix/OpenDKIM observability mail commissioned with daily/weekly timers; Better Stack successful-delivery heartbeat integration remains pending

Authoritative production documentation:

    docs/production/

## Current production application state

Production is deployed at `https://dacquadolce.com`. The running release is an operational fact and should be read from the production release metadata/deployment output rather than hard-coded into this README. Rebuilds and deployments always target an exact 40-character Git revision.

The current repository/rebuild target includes:

- customer registration, login, sessions, password reset, explicit email verification, and privileged MFA;
- customer profile/address management, site-wide appearance controls, and product-detail footer/theme controls;
- quote, cart, order, pricing, inventory, return/cancellation, assisted-sales, and policy governance;
- PT54 formal **Order Reviewed** checklist evidence plus cannot-fulfill customer-response holds before employee-controlled `Order Confirmed`;
- repo-managed catalog reconciliation with shared `Product Category -> Product Family -> Product Variant` identity, Essence **Automatic Rinse**, Origin **Ultra-Pure / Alkaline Plus**, and Refine 1.5/2.0 cu ft variants with repository-managed images;
- discontinued-product public retirement/replacement behavior while preserving historical product records;
- Operations console, Customer Inbox, Accounts & Address Book, User Access & Roles, Audit Log, and compact Pricing & Inventory governance;
- durable PostgreSQL communications with Website/Email source distinction, safe plain-text inbound rendering, non-clickable inbound/customer-supplied URLs, and advisory Postmark spam/SPF evidence when the provider actually supplies those headers;
- public support-form CSRF, rate limiting, an invisible honeypot, and field-specific FastAPI/Pydantic validation messages;
- provider-neutral automated-tax/payment commissioning foundations, with public hosted checkout still closed;
- PT52 keyboard/mobile/accessibility hardening and PT53 policy export/import portability for deliberate Production -> Local/Dev/Test policy synchronization without database cloning.

The authoritative production catalog baseline is under:

    backend/catalog/

Operational state such as product lifecycle, price history, inventory, accounts, orders, communications, approved claims/policies, and launch evidence is deliberately not reconstructed from the catalog manifest during deployment. Production recovery requires the production PostgreSQL state or an explicitly approved manual reconstruction of that state.

## Authority model

- Git is authoritative for application code, schema, deployment assets, and repository-managed catalog source.
- Production PostgreSQL is authoritative for live business/operational state, including approved customer policy versions.
- PT53 policy bundles are manual transport artifacts, not a second source of truth.
- AWS S3/Restic, once commissioned, is a disaster-recovery destination rather than an environment synchronization mechanism.

See `docs/PT53_POLICY_PORTABILITY_ENVIRONMENT_SYNC.md` for the safe policy portability workflow.

## Development policy

Century Solar (`~/Desktop/century-solar/`) is a read-only reference implementation.

Do not bulk rename or directly mutate Century Solar. Security, compliance, commerce, customer-portal, equipment, and operational functionality should be selectively ported and adapted to D'Acqua Dolce requirements.

## Run the application locally

D'Acqua Dolce uses separate FastAPI backend and React/Vite frontend development servers.

Canonical local ports and the host-vs-container PostgreSQL distinction are documented in `docs/LOCAL_DEVELOPMENT.md`.

### 1. Start the backend

From the repository root:

    cd backend

    .venv/bin/uvicorn app.main:app \
      --reload \
      --host 127.0.0.1 \
      --port 8000

Keep this terminal running.

The backend API is available at:

    http://127.0.0.1:8000

### 2. Start the frontend

Open a second terminal:

    cd ~/Desktop/dacqua-dolce/frontend
    npm run dev

Keep this terminal running.

### 3. Open D'Acqua Dolce

Open the application in a browser:

    http://127.0.0.1:15173

The Vite development server serves the frontend and forwards application API requests to the FastAPI backend.

> Run backend commands from `backend/` so the backend loads its local environment configuration correctly.
