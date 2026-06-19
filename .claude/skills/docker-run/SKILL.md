---
description: Run the full Bangla AI Customer Support stack via Docker Compose — Frontend, FastAPI backend, PostgreSQL, Prometheus, and Grafana. Use for production-like testing.
---

# Docker Run — Full Stack via Docker Compose

Brings up all services in containers: React frontend (port 80), FastAPI backend (port 8090), PostgreSQL, Prometheus (port 9090), and Grafana (port 3000).

## Prerequisites

- Docker Desktop running on Windows
- Working directory: project root

## Run

```powershell
cd deployment
docker compose up --build
```

First build takes 3–5 minutes. Subsequent runs are faster.

To run in the background:
```powershell
cd deployment
docker compose up --build -d
```

## Verify readiness

```powershell
# Backend health
for ($i = 0; $i -lt 60; $i++) {
    try { Invoke-RestMethod http://localhost:8090/ -TimeoutSec 2; break } catch { Start-Sleep 2 }
}
Invoke-RestMethod http://localhost:8090/
# Expected: { status = "online" }

# Frontend
Invoke-WebRequest http://localhost/ -UseBasicParsing | Select-Object StatusCode
# Expected: 200
```

## URLs

| Service | URL | Credentials |
|---|---|---|
| Customer chat (React) | http://localhost | — |
| API Swagger docs | http://localhost:8090/docs | — |
| Prometheus metrics | http://localhost:9090 | — |
| Grafana dashboards | http://localhost:3000 | admin / admin |

## Pre-seeded accounts (same as local dev)

| Role | Email | Password |
|---|---|---|
| Admin | admin@example.com | adminpassword123 |
| Agent | agent@example.com | agentpassword123 |

## Stop

```powershell
cd deployment
docker compose down
```

To also remove volumes (wipes the database):
```powershell
docker compose down -v
```

## Environment overrides

Set these in `deployment/.env` or pass as `docker compose --env-file`:

| Variable | Default | Notes |
|---|---|---|
| `LLM_PROVIDER` | `mock` | `openai` / `groq` / `huggingface` for real AI |
| `LLM_API_KEY` | `mock-key` | Required when provider is not `mock` |
| `JWT_SECRET` | default | Override in production |
| `POSTGRES_PASSWORD` | set in docker-compose.yml | Change before deploying |

## Logs

```powershell
# All services
docker compose logs -f

# Backend only
docker compose logs -f backend

# Frontend only
docker compose logs -f frontend
```

## Notes

- The Docker stack uses PostgreSQL instead of SQLite.
- The backend automatically runs `alembic` (or `create_all`) on startup — no manual migration needed.
- Sample orders and users are seeded on first startup.
- The `chroma_db` vector store is persisted in a named Docker volume.
