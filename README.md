# Skripts

Monorepo-Basisstruktur für die Work Orders **W00–W11** mit drei Apps und gemeinsamen Packages.

## Verzeichnisstruktur

```text
.
├── apps
│   ├── api
│   │   ├── pyproject.toml
│   │   └── src/api
│   │       ├── __init__.py
│   │       └── main.py
│   ├── web
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── src/main.ts
│   └── workers
│       ├── pyproject.toml
│       └── src/workers
│           ├── __init__.py
│           └── main.py
├── packages
│   ├── config
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── src/index.ts
│   ├── types
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── src/index.ts
│   └── utils
│       ├── package.json
│       ├── tsconfig.json
│       └── src/index.ts
├── .github/workflows/ci.yml
├── .env.example
└── docker-compose.yml
```

## Konsistenz zu Work Orders W00–W11

| Work Order | Zielpfad |
|---|---|
| W00 | Root-Bootstrap: `README.md`, `.env.example`, `docker-compose.yml`, `.github/workflows/ci.yml` |
| W01 | API-App in `apps/api` |
| W02 | Worker-App in `apps/workers` |
| W03 | Web-App in `apps/web` |
| W04 | Shared Config Package in `packages/config` |
| W05 | Shared Types Package in `packages/types` |
| W06 | Shared Utils Package in `packages/utils` |
| W07 | Python Packaging über `apps/*/pyproject.toml` |
| W08 | TypeScript App Build über `apps/web/tsconfig.json` |
| W09 | TypeScript Package Builds über `packages/*/tsconfig.json` |
| W10 | Lokale Orchestrierung über `docker-compose.yml` |
| W11 | CI-Smoketests und Build-Checks in `.github/workflows/ci.yml` |

## Setup

1. Beispiel-Umgebung kopieren:
   ```bash
   cp .env.example .env
   ```
2. Python-Services lokal starten (Smoke Test):
   ```bash
   python apps/api/src/api/main.py
   python apps/workers/src/workers/main.py
   ```
3. Web-App lokal bauen und starten:
   ```bash
   cd apps/web
   npm install
   npm run build
   npm run start
   ```

## Run mit Docker Compose

```bash
docker compose up --build
```

## CI

Die CI (`.github/workflows/ci.yml`) führt aus:
- Python Smoke-Starts für API + Workers
- TypeScript Build für `apps/web`
- TypeScript Builds für alle `packages/*`
