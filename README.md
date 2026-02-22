# Skripts Monorepo (Bootstrap)

Dieses Repository enthält eine minimale Startstruktur für:

- `apps/api` (FastAPI)
- `apps/workers` (Celery Worker + Beat)
- `apps/web` (Node HTTP App)
- `packages/*` (gemeinsame Pakete)

## Struktur

```text
.
├── apps
│   ├── api
│   ├── web
│   └── workers
├── packages
│   ├── contracts
│   ├── shared
│   └── utils
├── docker-compose.yml
└── .env.example
```

## Quickstart

1. Umgebungsdatei anlegen:

   ```bash
   cp .env.example .env
   ```

2. Alle Basisdienste starten:

   ```bash
   docker compose up --build
   ```

3. Healthchecks prüfen:

   - API: <http://localhost:8000/health>
   - Web: <http://localhost:3000/health>

## Dienste aus `docker-compose.yml`

- `postgres`
- `redis`
- `api`
- `worker`
- `beat`
- `web`
