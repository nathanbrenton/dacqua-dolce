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
- Postmark transactional email commissioned for application mail
- observability report email delivery/timers still pending

Authoritative production documentation:

    docs/production/

## Current production application state

The public production application includes:

- canonical public origin `https://dacquadolce.com`;
- six canonical water-filtration products bootstrapped from repo-managed catalog data;
- customer registration, login, sessions, password reset, and explicit email verification;
- privileged MFA;
- customer profile and address management;
- customer account Appearance controls with visual-theme and light/dark preferences;
- quote, cart, order, pricing-policy, and inventory foundations;
- Operations console for staff workflows;
- web administration of `employee`, `manager`, and `administrator` roles;
- CLI-only management of the `developer` role;
- audit events and email-delivery metadata;
- Postmark-backed transactional email.

The authoritative production catalog baseline is under:

    backend/catalog/

Operational state such as price history, inventory quantities, approved claims, and jurisdiction rules is deliberately not reset from the catalog manifest during deployment.

## Development policy

Century Solar (`~/Desktop/century-solar/`) is a read-only reference implementation.

Do not bulk rename or directly mutate Century Solar. Security, compliance, commerce, customer-portal, equipment, and operational functionality should be selectively ported and adapted to D'Acqua Dolce requirements.

## Run the application locally

D'Acqua Dolce uses separate FastAPI backend and React/Vite frontend development servers.

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

    http://localhost:5173

The Vite development server serves the frontend and forwards application API requests to the FastAPI backend.

> Run backend commands from `backend/` so the backend loads its local environment configuration correctly.
