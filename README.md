# Skripts

Monorepo bootstrap for the Section 19 service layout.

## Repository layout

```text
apps/
  api/
  workers/
  web/
packages/
  schemas/
  policy/
  graph/
  llm/
  eval/
```

## Service responsibilities

- **apps/api**: API surface area and request orchestration.
- **apps/workers**: asynchronous/background job execution.
- **apps/web**: frontend entrypoint and UI shell.
- **packages/schemas**: shared payload and model definitions.
- **packages/policy**: authorization and policy enforcement logic.
- **packages/graph**: workflow graph construction/execution.
- **packages/llm**: LLM provider abstraction layer.
- **packages/eval**: evaluation harnesses and scoring workflows.

## Local boot instructions

1. Copy environment template:
   ```bash
   cp .env.example .env
   ```
2. Start all services:
   ```bash
   docker compose up --build
   ```
3. Optional local smoke checks (without Docker):
   ```bash
   python apps/api/api/main.py
   python apps/workers/workers/main.py
   python packages/schemas/schemas/main.py
   python packages/policy/policy/main.py
   python packages/graph/graph/main.py
   python packages/llm/llm/main.py
   python packages/eval/eval/main.py
   node --check apps/web/src/main.js
   ```

## CI and path consistency

- CI workflow: `.github/workflows/ci.yml`
- Docker orchestration: `docker-compose.yml`
- Environment template: `.env.example`

All path references in this README and CI map directly to the filesystem names above.
