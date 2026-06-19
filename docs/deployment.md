# Deployment and Operations Guide

This document covers production deployment configurations and the operational workflow for agents and administrators.

---

## Environment Variables

Create a `.env` file in the repository root (or set these in your container/Kubernetes environment). All values shown are the built-in defaults.

```env
# Security
JWT_SECRET=supersecretjwtsecretkeychangeinproduction123456789
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ADMIN_INITIAL_PASSWORD=adminpassword123

# Database
# SQLite (dev):
DATABASE_URL=sqlite:///./support_platform.db
# PostgreSQL (production):
# DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<dbname>

# ChromaDB
CHROMA_PERSIST_DIRECTORY=./chroma_db

# LLM Provider — set to "mock" for heuristic-only mode
LLM_PROVIDER=mock          # mock | openai | groq | huggingface
LLM_API_KEY=mock-key
LLM_MODEL_NAME=gpt-4o-mini

# Embeddings
EMBEDDING_MODEL_NAME=sentence-transformers/LaBSE

# Server
HOST=0.0.0.0
PORT=8090
DEBUG=true
```

> **Important:** Always replace `JWT_SECRET` and `ADMIN_INITIAL_PASSWORD` with strong random values before any public-facing deployment.

---

## Production Deployment Checklist

### 1. Database

Switch from SQLite to a PostgreSQL cluster:

```env
DATABASE_URL=postgresql://support_user:strongpassword@db-host:5432/support_db
```

The application uses SQLAlchemy and requires no schema migrations — `Base.metadata.create_all()` runs on startup.

### 2. LLM Provider

To use a real LLM instead of heuristic fallbacks, set `LLM_PROVIDER` to one of the supported values:

| Provider       | `LLM_PROVIDER` | `LLM_API_KEY`        | `LLM_MODEL_NAME` example        |
|----------------|----------------|----------------------|---------------------------------|
| OpenAI         | `openai`       | OpenAI API key       | `gpt-4o-mini`                   |
| Groq           | `groq`         | Groq API key         | `llama-3.1-8b-instant`          |
| HuggingFace    | `huggingface`  | HF access token      | `google/flan-t5-large`          |
| vLLM (local)   | `openai`       | any string           | your hosted model name          |

vLLM exposes an OpenAI-compatible endpoint — point `LLM_API_KEY` at your vLLM token and override the base URL if needed.

Non-200 responses (rate limits, auth failures, server errors) from all providers are logged at `ERROR` level in the backend logs. Monitor these to detect quota exhaustion.

### 3. Embedding Model

The default `LaBSE` model is downloaded from HuggingFace Hub on first startup. To avoid cold-start delays in production, pre-download and mount the model:

```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/LaBSE')"
```

Set `HF_TOKEN` to increase HuggingFace Hub rate limits:
```env
HF_TOKEN=hf_your_token_here
```

### 4. Secret Rotation

- Rotate `JWT_SECRET` and re-issue tokens to all active sessions.
- Store secrets in a secrets manager (AWS Secrets Manager, Vault, Kubernetes Secrets) rather than plain `.env` files in production.

### 5. Frontend API URL

The React frontend currently hardcodes `http://localhost:8090` as the backend URL. For deployments on a different host or port, update the fetch URLs in:

- `frontend/src/pages/CustomerChat.jsx` — `/api/chat`, `/api/voice/stt`, `/api/voice/tts`, `/api/feedback`
- `frontend/src/pages/Dashboard.jsx` — analytics and ticket endpoints

A recommended pattern is to set `VITE_API_BASE_URL` in a `.env` file at the frontend root and reference it via `import.meta.env.VITE_API_BASE_URL`.

---

## Docker Compose

Starts the full stack (backend, frontend, PostgreSQL, Prometheus, Grafana):

```bash
cd deployment
docker-compose up --build -d
```

| Service              | URL                          |
|----------------------|------------------------------|
| Frontend             | `http://localhost`           |
| Backend API + Docs   | `http://localhost:8090/docs` |
| Prometheus           | `http://localhost:9090`      |
| Grafana              | `http://localhost:3000`      |

---

## Telemetry Setup

### Prometheus

Prometheus scrapes `/api/metrics` every 15 seconds (configured in `deployment/prometheus.yml`).

1. Open `http://localhost:9090`.
2. Navigate to **Status → Targets** and verify `customer_support_backend` shows **UP**.

### Grafana

1. Open `http://localhost:3000` (credentials: `admin` / `admin`).
2. Go to **Configuration → Data Sources → Add data source → Prometheus**.
3. Set the URL to `http://prometheus:9090` and click **Save & Test**.
4. Build panels for request rate, response latency, ticket creation rate, and sentiment distribution.

---

## User Operations Guide

### A. Customer Portal

1. Navigate to `http://localhost:5173` (or your deployed domain).
2. Type a question in Bangla, English, or Banglish in the chat input and press **Enter** or click **Send**.
   - The input and Send button are disabled while a response is loading to prevent duplicate submissions.
3. Click the **Speak** button to dictate a question using your microphone. The browser captures 2 seconds of audio via the `MediaRecorder` API and sends it to the STT endpoint. The transcription populates the input field — review it and press **Send**.
4. Click the **Speaker** icon on any bot message to hear it read aloud (TTS).
5. If the system cannot resolve your query automatically (low knowledge-base confidence or highly negative sentiment), a **Ticket Escalated** card appears in the left panel with the assigned ticket ID.
6. At the end of a conversation, rate the response with the thumbs-up / thumbs-down widget.

### B. Support Agent Workflow

1. Open the **Agent Portal** link in the top navigation bar.
2. Log in with `agent@example.com` / `agentpassword123` (or your own agent credentials).
3. On the **Open Tickets** tab, the queue shows all unresolved tickets ordered by creation time with priority badges.
4. Click **Start Working** on a ticket to assign it to yourself and change its status to `In Progress`.
5. After resolving the issue, click the green check to set status to `Resolved` and remove it from the active queue.

### C. Administrator Tasks

1. Log in with `admin@example.com` / `adminpassword123`.
2. **Insights & Analytics** tab: review conversation volume, resolution rate, average satisfaction score, and language/sentiment distribution trends.
3. **Seed Knowledge Base** tab: drag-and-drop a corporate PDF, FAQ CSV, or text document and click **Ingest File**. The pipeline chunks the file, embeds each chunk with LaBSE, and stores vectors in ChromaDB. New documents are immediately searchable by the FAQ agent.
4. **Ticket Management** tab: filter by status or priority, reassign tickets to other agents, and close resolved issues.

---

## Kubernetes

```bash
cd deployment/k8s
kubectl apply -f db-deployment.yaml
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f ingress.yaml
```

With Helm:

```bash
cd deployment/helm
helm install bangla-support ./
```

Configure the backend `PORT` and database URL via `values.yaml` or `--set` overrides before deploying.
