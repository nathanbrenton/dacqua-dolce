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
- Vultr
- Nginx
- Postmark
- pgBackRest
- AWS S3
- Prometheus / Grafana / Loki observability

## Development policy

Century Solar (`~/Desktop/century-solar/`) is a read-only reference
implementation.

Do not bulk rename or directly mutate Century Solar. Security, compliance,
commerce, customer-portal, equipment, and operational functionality should be
selectively ported and adapted to D'Acqua Dolce requirements.
