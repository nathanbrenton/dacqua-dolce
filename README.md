# D'Acqua Dolce

**Water, Elevated.**

D'Acqua Dolce is a mobile-first water-filtration commerce and customer
lifecycle platform.

## Application stack

### Frontend
- TypeScript
- React
- Vite

### Backend
- Python
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL

### Production infrastructure
- Vultr / Debian 13
- Nginx + Let's Encrypt/Certbot
- PostgreSQL 17
- Prometheus / Alertmanager / Grafana / Loki / Alloy / Monit
- Better Stack external monitoring
- Local PostgreSQL backup + full restore validation
- Restic encryption layer prepared; AWS S3 off-host repository pending
- Final outbound SMTP/report-delivery architecture pending

Authoritative production documentation:

    docs/production/

## Development policy

Century Solar (`~/Desktop/century-solar/`) is a read-only reference
implementation.

Do not bulk rename or directly mutate Century Solar. Security, compliance,
commerce, customer-portal, equipment, and operational functionality should be
selectively ported and adapted to D'Acqua Dolce requirements.


## Run the Application Locally

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
