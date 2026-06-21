# Docker Setup

Run the entire stack — backend, frontend, PostgreSQL, Prometheus, and Grafana — with a single command.

## Start

```bash
cd deployment
docker-compose up --build
```

## Services

| Service | URL | Notes |
|---|---|---|
| Frontend (Nginx) | [http://localhost](http://localhost) | React app |
| Backend (FastAPI) | [http://localhost:8090](http://localhost:8090) | API server |
| API Swagger | [http://localhost:8090/docs](http://localhost:8090/docs) | Interactive API docs |
| Prometheus | [http://localhost:9090](http://localhost:9090) | Metrics scraper |
| Grafana | [http://localhost:3000](http://localhost:3000) | Dashboards (admin / admin) |

## Stop

```bash
docker-compose down
```

To also remove volumes (database + vector store):

```bash
docker-compose down -v
```

## Environment Variables in Docker

Create a `deployment/.env` file (or pass vars directly to Compose) before running:

```env
LLM_PROVIDER=openrouter
LLM_API_KEY=sk-or-v1-...
LLM_MODEL_NAME=nvidia/nemotron-3-super-120b-a12b:free
JWT_SECRET=change-me-in-production
```

See [Environment Variables](environment.md) for the full reference.
