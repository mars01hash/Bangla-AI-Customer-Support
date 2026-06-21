# Project Title: Bangla AI Customer Support Platform

**Authors:**

| Name | Student ID |
|---|---|
| Muntasir | [YOUR STUDENT ID] |

**Submission Date:** 25/06/2026

**Advanced Training on Semiconductor and ICT Technology — BRAC University**

---

## Table of Contents

1. [Introduction](#1-introduction)
   - 1.1 Brief Introduction
   - 1.2 Problem Statement
   - 1.3 Objectives
2. [Dataset and Preparation](#2-dataset-and-preparation)
   - 2.1 Dataset Description
   - 2.2 Data Access
   - 2.3 Preprocessing
3. [Methodology](#3-methodology)
   - 3.1 Course Techniques Used
   - 3.2 Model Architecture
   - 3.3 Training Strategy
4. [Experiments and Results](#4-experiments-and-results)
   - 4.1 Experiment Tracking
   - 4.2 Evaluation Results
5. [Prediction App and Docker](#5-prediction-app-and-docker)
   - 5.1 Prediction Pipeline
   - 5.2 Prediction UI
   - 5.3 Docker Serving
6. [Repository and Reproducibility](#6-repository-and-reproducibility)
   - 6.1 Repository Structure
   - 6.2 GitHub Rules
   - 6.3 Reproducibility
7. [Limitations and Future Work](#7-limitations-and-future-work)
   - 7.1 Limitations
   - 7.2 Future Improvements
8. [Conclusion](#8-conclusion)

---

## 1. Introduction

### 1.1 Brief Introduction

This project belongs to the **NLP Customer Support** domain. It is a production-grade, multi-tenant SaaS chatbot platform built for Bangladeshi ecommerce businesses.

The type of ML/deep-learning system built is a **Retrieval-Augmented Generation (RAG) pipeline** powered by a multilingual transformer model (LaBSE) combined with a LangGraph-based intent-routing agent and provider-agnostic large language model (LLM) integration.

The main purpose is to automate customer support for ecommerce stores in Bangladesh, where customers communicate in Bangla, English, and Banglish (romanised Bangla). The platform allows any ecommerce store to embed an AI chat widget on their website, manage their own knowledge base, and route unresolved issues to human support agents.

The final system accepts customer text messages in any of the three scripts, classifies intent across 8 categories (greeting, FAQ, product, order tracking, order placement, billing, complaint, escalation), retrieves relevant answers from a per-tenant vector store, generates a response via an LLM, and — when needed — automatically creates a structured support ticket for a human agent.

---

### 1.2 Problem Statement

**Real-world problem:** Bangladeshi ecommerce customer support is expensive and slow. Customers write in Bangla, English, and Banglish interchangeably, and existing chatbots either support only English or require explicit language selection before understanding input. Businesses are forced to staff human agents for routine queries — order tracking, product questions, billing issues — that can be automated.

- **Input:** A customer text message in Bangla, English, or Banglish (e.g., "আমার অর্ডার কোথায়?", "Where is my order?", or "ami order korchi kintu status dekhte parchina")
- **Output:** An intent-classified, contextually relevant AI response — order status fetched from DB, FAQ answer retrieved from knowledge base, or a support ticket created automatically
- **Who uses it:** Ecommerce businesses embed the widget on their website (store admins); their customers chat anonymously; human agents handle escalated tickets
- **Why it matters:** 80%+ of customer queries are repetitive (order status, return policy, product specs). Automating these in Bangla/English/Banglish reduces support costs and improves response time from hours to seconds

---

### 1.3 Objectives

1. Build a multilingual NLP chatbot that correctly classifies customer intent across 8 categories in Bangla, English, and Banglish without requiring translation
2. Implement a RAG pipeline using LaBSE sentence embeddings and ChromaDB so responses are grounded in each store's actual knowledge base
3. Build a multi-tenant architecture where each ecommerce store has isolated knowledge, agents, and tickets — accessed via API key
4. Serve the complete chat prediction pipeline via Docker (FastAPI backend + React frontend + PostgreSQL + Prometheus)
5. Ensure full reproducibility: a fresh clone + `.env` setup + `docker compose up` runs the entire platform end-to-end

---

## 2. Dataset and Preparation

### 2.1 Dataset Description

This project does not use an external pre-existing dataset. The data is the platform's own **knowledge base** — Q&A pairs created by store admins and automatically indexed into the vector store.

| Property | Value |
|---|---|
| Dataset name | Platform knowledge base (auto-seeded + admin-managed) |
| Source | Generated and seeded on first application startup |
| Input type | Text — Bangla, English, Banglish |
| Number of seeded Q&A pairs | 20+ across 2 demo stores (ShopBD, FashionBD) |
| Number of products (demo) | 12 (fashion, electronics, accessories, shoes) |
| Intent categories (output classes) | 8 (greeting, faq, product, order, order_placement, billing, complaint, escalation) |
| Target variable | Intent label + generated natural-language response |

Additionally, the system's SQLite/PostgreSQL database holds `Order`, `Ticket`, `User`, `Tenant`, and `Product` tables — all auto-populated during initial seeding via `app/main.py`.

---

### 2.2 Data Access

No external dataset download is required. Data is generated automatically:

1. **Demo database** — On first run, `app/main.py` calls `seed_database()` which creates all tables and inserts pre-seeded tenants, users, products, and knowledge base entries into SQLite (`support_platform.db`)
2. **LaBSE embedding model** — Downloaded automatically by `sentence-transformers` on first backend startup from HuggingFace Hub (~500MB). No manual action needed
3. **ChromaDB vector store** — Built at runtime when store admins add knowledge base entries via the Store Admin panel. Persisted to `chroma_db/` (gitignored, regenerated per-deployment)

Neither `support_platform.db` nor `chroma_db/` are committed to GitHub. The `backend/requirements.txt` and `.env.example` are the only setup artefacts committed.

---

### 2.3 Preprocessing

Text preprocessing is applied at two stages:

**At knowledge base ingestion** (`backend/app/rag/ingestion.py`):
- Text chunking for long documents (PDF, DOCX, Excel upload support)
- Encoding via LaBSE tokenizer (internal to `sentence-transformers`)
- Embedding generation: 768-dimensional float vector per chunk
- Storage in ChromaDB with `tenant_id` metadata for per-tenant filtering

**At inference / query time** (`backend/app/agents/nodes.py`):
- Whitespace stripping and lowercase normalisation
- Script detection: Unicode codepoint range check distinguishes Bangla (U+0980–U+09FF) from Latin script — sets `detected_language` in agent state
- Keyword pattern matching across Bangla, English, and Banglish token lists for intent pre-classification
- Sentiment scan: negative keyword patterns (Bangla + English) flag complaint intent
- Query embedded via LaBSE → cosine similarity search in ChromaDB (threshold 0.3)
- Retrieved context injected into LLM prompt

No train/validation/test split is applied — the model (LaBSE) is used as a frozen pre-trained backbone; no custom training loop is required.

---

## 3. Methodology

### 3.1 Course Techniques Used

| Technique | Where Used |
|---|---|
| Transfer Learning | `backend/app/rag/embedder.py` — LaBSE loaded as a frozen pre-trained model via `sentence-transformers` |
| Transformer Architecture (BERT) | LaBSE is a 12-layer BERT-based multilingual transformer; all semantic similarity runs through its 768-dim output |
| RAG (Retrieval-Augmented Generation) | `backend/app/rag/vectorstore.py`, `ingestion.py` — ChromaDB nearest-neighbour search feeds retrieved context into LLM prompt |
| NLP — Intent Classification | `backend/app/agents/nodes.py` — keyword pattern router across 8 intent categories in 3 languages |
| NLP — Sentiment Analysis | `backend/app/agents/nodes.py` — negative sentiment detection triggers auto-escalation |
| NLP — Language Detection | `backend/app/agents/nodes.py` — Unicode script range check, result propagated through agent state |
| Multi-turn Dialogue State | `backend/app/agents/nodes.py` — `order_placement` node tracks collected fields via conversation history inspection |
| LangGraph Agent Workflow | `backend/app/agents/graph.py` — LangGraph `StateGraph` with conditional routing edges |
| Dockerized Prediction App | `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` |
| REST API Model Serving | `backend/app/api/endpoints.py` — FastAPI serving the chat pipeline at `/api/chat` and `/api/widget/chat` |
| Prometheus Monitoring | `backend/app/main.py` — `prometheus-client` metrics exposed at `/metrics` |

---

### 3.2 Model Architecture

**Embedding Model — LaBSE (Language-agnostic BERT Sentence Embedding)**

| Property | Value |
|---|---|
| Model name | `sentence-transformers/LaBSE` |
| Architecture | BERT-base (12 transformer layers, 12 attention heads) |
| Hidden dimension | 768 |
| Pre-training | Trained on 109 languages including Bengali using translation ranking and MLM objectives |
| Output | 768-dimensional L2-normalised sentence embedding |
| Similarity metric | Cosine similarity |
| RAG retrieval threshold | 0.3 (responses below this score skip context injection) |
| Usage | Frozen — used as a feature extractor only, no fine-tuning |

**Agent Framework — LangGraph StateGraph**

```
User Message
     │
     ▼
Language & Sentiment Detection Node
     │
     ▼
Router Node  (keyword-based intent classifier)
  ├── greeting        → Greeting Node
  ├── faq             → FAQ Node (ChromaDB RAG, tenant-scoped, k=3)
  │                         └── [cosine < 0.3] → Escalation Node
  ├── product         → Product Node
  ├── order           → Order Status Node (SQLAlchemy DB lookup)
  ├── order_placement → Order Placement Node (multi-turn state machine)
  ├── billing         → Billing Node
  ├── complaint       → Complaint Node → Escalation Node
  └── escalation      → Escalation Node (creates Ticket row)
```

**LLM Layer** — Provider-agnostic `query_llm_api()` in `nodes.py` supports:
- OpenAI (`gpt-4o-mini`)
- Groq (`llama-3.3-70b-versatile`)
- OpenRouter (free models available)
- HuggingFace Inference API
- Mock mode (no API key needed — heuristic fallbacks only)

---

### 3.3 Training Strategy

This project uses LaBSE as a **frozen pre-trained model** — no custom model training loop is required. The "training" in this project is the knowledge base ingestion pipeline:

1. Store admin adds Q&A pairs via the Store Admin Panel
2. Each entry is embedded by LaBSE and stored in ChromaDB with `tenant_id` metadata
3. At query time, the customer's message is embedded and the top-3 nearest neighbours are retrieved by cosine similarity
4. Retrieved chunks are injected into the LLM system prompt as context

**Hyperparameters used:**
- `k = 3` (number of RAG results retrieved per query)
- `similarity_threshold = 0.3` (minimum cosine similarity for RAG context to be used)
- `embedding_dimension = 768` (fixed by LaBSE)
- `LLM_PROVIDER = openrouter` (configurable via `.env`)

The best "model" selection is implicit: LaBSE was chosen over alternatives (multilingual-e5, paraphrase-multilingual-mpnet) because it has the strongest performance on Bangla–English bilingual sentence similarity benchmarks while being freely available on HuggingFace.

---

## 4. Experiments and Results

### 4.1 Experiment Tracking

This project uses a **pre-trained frozen transformer** (LaBSE) rather than a custom-trained model, so a conventional MLflow training-run tracking pipeline is not applicable. System behaviour was validated through:

- **Functional intent routing tests** — `tests/test_chat_agent.py` exercises all 8 intent branches
- **Auth and ticket API tests** — `tests/test_auth.py`, `tests/test_tickets.py`
- **Manual benchmark** — `backend/benchmark_embeddings.py` measures embedding latency and retrieval quality on sample Bangla/English queries

Key observations from benchmark runs:

| Experiment | Observation |
|---|---|
| LaBSE vs mock embeddings | LaBSE produces semantically meaningful neighbours; mock (SHA-256 hash fallback) produces random neighbours — confirmed RAG quality depends on real model |
| Cosine threshold 0.3 vs 0.5 | Threshold 0.3 returns relevant results for paraphrased queries; 0.5 is too strict for Banglish variants |
| k=3 vs k=5 RAG results | k=3 keeps prompt size manageable; k=5 added noise for short FAQ answers |

---

### 4.2 Evaluation Results

**Intent Routing — Test Coverage**

| Intent | Test Inputs | Result |
|---|---|---|
| Greeting | "hello", "হ্যালো", "hi there" | Correct greeting response |
| Order tracking | Valid ID (ORD-XXXXX), invalid ID | Correct status / not-found message |
| Complaint → Escalation | Negative sentiment messages | Ticket created automatically |
| Order placement | Buy intent → multi-turn name/phone/address | Order row created in DB |
| FAQ | Knowledge base query | RAG-retrieved answer returned |

**System Performance Metrics**

| Metric | Value |
|---|---|
| Heuristic intent response latency | 200–500 ms |
| LLM-backed intent response latency | 1–3 s (provider-dependent) |
| ChromaDB vector search latency | < 50 ms |
| LaBSE embedding latency (single query) | ~80–150 ms (CPU) |
| Test suite pass rate | 100% (all 3 test files pass) |
| Supported languages | Bangla, English, Banglish |
| Intent categories | 8 |
| Multi-tenant isolation | API-key scoped ChromaDB + DB queries |

![Chat Widget](screenshots/chat_widget.png)
*Figure 1 — Chat widget showing Bangla response to a customer query*

![Order Tracking](screenshots/order_tracking.png)
*Figure 2 — Order tracking response generated from DB lookup*

---

## 5. Prediction App and Docker

### 5.1 Prediction Pipeline

The end-to-end prediction pipeline for a customer query:

1. **Input** — Customer types a message in the chat widget (embedded on any ecommerce site) or the standalone CustomerChat page. The widget sends `POST /api/widget/chat` with `{message, session_id, preferred_language}` and `X-Api-Key` header
2. **Tenant resolution** — Backend resolves the store from `X-Api-Key` and injects `tenant_id` into agent state
3. **Language detection** — Unicode script range check identifies Bangla vs Latin; `detected_language` stored in state
4. **Sentiment scan** — Negative keyword patterns flag complaint/escalation path early
5. **Intent classification** — Router node applies keyword pattern matching across Bangla, English, Banglish lists → routes to one of 8 handler nodes
6. **Context retrieval (FAQ path)** — LaBSE embeds the query → ChromaDB cosine search → top-3 Q&A pairs retrieved filtered by `tenant_id`
7. **LLM generation** — Selected node constructs a prompt (system instruction + retrieved context + conversation history) and calls `query_llm_api()`
8. **Output** — JSON response `{reply, intent, session_id}` returned to the widget; displayed to customer in real time
9. **Side effects** — Order placement creates an `Order` row; complaints create a `Ticket` row visible to agents in the dashboard

---

### 5.2 Prediction UI

The prediction interface is a custom **React 18 + Vite + Tailwind CSS** frontend — not Streamlit or Gradio, but a production-ready web application.

Two chat interfaces are provided:

**ChatWidget** (`frontend/src/components/ChatWidget.jsx`) — A floating bubble widget that any ecommerce site can embed via a `<script>` tag. Features: language toggle (Bangla / English), auto-send on order ID prefill, real-time message display.

**CustomerChat** (`frontend/src/pages/CustomerChat.jsx`) — A full-page standalone chat demo for testing all intents.

Additional panels built on the same prediction backend:
- **Store Admin Panel** — Knowledge base management, embed code, agent management
- **Agent Dashboard** — Ticket queue, analytics, order management
- **Super Admin Panel** — Multi-tenant management, API key rotation
- **ShopBD Ecommerce Storefront** — Full browse → cart → checkout → payment → order-in-chat demo

![Store Admin Panel](screenshots/store_admin_panel.png)
*Figure 3 — Store Admin Panel: Knowledge Base tab*

![Agent Dashboard](screenshots/agent_dashboard.png)
*Figure 4 — Agent Dashboard: ticket queue with assigned store filter*

![Ecommerce Storefront](screenshots/ecommerce_storefront.png)
*Figure 5 — ShopBD ecommerce storefront with integrated chat widget*

---

### 5.3 Docker Serving

The repository contains `backend/Dockerfile`, `frontend/Dockerfile`, and `docker-compose.yml` at the project root. The full prediction stack is containerised and launched with a single command:

```bash
cp .env.example .env   # add your LLM_API_KEY
docker compose up --build
```

This starts 5 services:

| Service | Port | Description |
|---|---|---|
| FastAPI backend | 8090 | Chat prediction API + REST endpoints |
| React frontend | 80 | Chat widget + admin panels |
| PostgreSQL | 5432 | Production database (replaces SQLite) |
| Prometheus | 9090 | Request metrics scraper |
| Grafana | 3000 | Metrics dashboard (admin / admin) |

The LaBSE model (~500MB) is downloaded and baked into the backend Docker image at build time via the `sentence-transformers` package. Subsequent starts are fast as the model is cached in the image layer.

![Super Admin Panel](screenshots/super_admin_panel.png)
*Figure 6 — Super Admin Panel running via Docker, showing tenant management*

---

## 6. Repository and Reproducibility

### 6.1 Repository Structure

```
nlp-customer-support-bangla/
├── README.md                       # Project overview + setup + screenshots
├── final_report.md                 # This report
├── .env.example                    # Environment variable template
├── .gitignore                      # Excludes venv, .env, *.db, chroma_db, *.log
├── docker-compose.yml              # Full-stack Docker orchestration
├── backend/
│   ├── Dockerfile                  # Backend container (FastAPI + LaBSE)
│   ├── requirements.txt            # Python dependencies
│   └── app/
│       ├── agents/
│       │   ├── graph.py            # LangGraph StateGraph
│       │   ├── nodes.py            # All 8 intent handler nodes
│       │   └── state.py            # AgentState TypedDict
│       ├── rag/
│       │   ├── embedder.py         # LaBSE sentence embedder
│       │   ├── vectorstore.py      # ChromaDB + in-memory fallback
│       │   └── ingestion.py        # Document chunking + indexing
│       ├── api/endpoints.py        # All FastAPI routes
│       ├── auth.py                 # JWT + API-key auth + role guards
│       ├── models.py               # SQLAlchemy ORM models
│       ├── schemas.py              # Pydantic schemas
│       ├── config.py               # Settings from .env
│       └── main.py                 # App startup + DB seeding
├── frontend/
│   ├── Dockerfile                  # Frontend container (Nginx + React build)
│   └── src/
│       ├── pages/                  # SuperAdmin, StoreAdmin, Dashboard, Chat, Ecommerce
│       └── components/ChatWidget.jsx
├── deployment/
│   ├── docker-compose.yml          # Alternative deployment config
│   ├── prometheus.yml              # Prometheus scrape config
│   └── k8s/                        # Kubernetes manifests
├── screenshots/                    # UI screenshots for README and report
└── tests/
    ├── test_auth.py
    ├── test_chat_agent.py
    └── test_tickets.py
```

---

### 6.2 GitHub Rules

The following are **not committed** to the repository:

- `backend/support_platform.db` — SQLite database (auto-created on startup)
- `backend/chroma_db/` — ChromaDB vector store (rebuilt from knowledge base entries)
- `backend/venv/` — Python virtual environment
- `.env` — API keys and secrets (only `.env.example` is committed)
- `*.log` — Runtime log files
- `backend/uvicorn_*.txt` — Server output files
- `frontend/node_modules/` — Node dependencies
- `__pycache__/`, `*.pyc` — Python bytecode cache

All of the above are covered by `.gitignore`.

---

### 6.3 Reproducibility

A reviewer can reproduce the full system from a fresh clone in two ways:

**Option A — Docker (recommended)**
1. Clone the repository
2. Copy `.env.example` to `.env` and set `LLM_PROVIDER` and `LLM_API_KEY`
3. Run `docker compose up --build`
4. Open `http://localhost` — the full platform is running
5. Log in with any pre-seeded account (see README for credentials)
6. Test chat at `http://localhost` (no login) or via the ecommerce storefront

**Option B — Local development**
1. Clone the repository
2. `cd backend && python -m venv venv && venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env`, configure LLM provider
5. `uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload`
6. In a separate terminal: `cd frontend && npm install && npm run dev`
7. Open `http://localhost:5173`

The database and vector store are initialised automatically on first startup. No manual data download or setup script is needed.

Run tests:
```bash
cd backend && venv\Scripts\activate
pytest ../tests/ -v
```

---

## 7. Limitations and Future Work

### 7.1 Limitations

- **LLM dependency for full quality** — Setting `LLM_PROVIDER=mock` disables all external LLM calls. Heuristic fallbacks handle routing, but response quality degrades significantly for FAQ and open-ended queries. Full quality requires a live API key (Groq free tier is available)
- **Heuristic intent classification** — Intent routing is keyword-pattern based, not ML-based. Unusual phrasing, heavy code-switching, or novel Banglish constructions may misroute to FAQ or escalation
- **SQLite not production-safe** — The default `DATABASE_URL=sqlite:///./support_platform.db` does not support concurrent writes. PostgreSQL (configured via Docker) is needed for any real deployment
- **ChromaDB not persistent across container restarts** — Vector store resets when the container is restarted without a Docker volume mount. Knowledge base entries must be re-added via the Store Admin panel after a clean restart
- **No cross-session chat history** — Conversation history lives in browser memory. Refreshing the page starts a new session; customers cannot retrieve previous conversations
- **Telegram webhook requires public HTTPS URL** — Local development must use polling mode (`python telegram_poll.py`) or ngrok tunnelling

---

### 7.2 Future Improvements

- **Supervised intent classifier** — Collect labelled intent data from real chat logs and train a lightweight classifier (e.g., fine-tune a smaller multilingual model like `multilingual-e5-small`) to replace the keyword-pattern router
- **LaBSE fine-tuning on Banglish** — Fine-tune LaBSE on a Bangladeshi ecommerce domain corpus to improve embedding quality for highly code-switched input
- **Persistent chat sessions** — Store conversation history in the database so customers can resume conversations across sessions
- **Voice input/output** — `gTTS` and `SpeechRecognition` are already in `requirements.txt`; a voice interface for rural Bangladeshi users who prefer spoken interaction is a natural extension
- **WebSocket for real-time agent handoff** — Replace the current polling model for agent ticket updates with WebSocket push notifications
- **Advanced Banglish normalisation** — Add a dedicated Banglish-to-Bangla transliteration pre-processing step to improve embedding quality for heavily romanised input

---

## 8. Conclusion

This project addressed the real problem of multilingual customer support for Bangladeshi ecommerce, where customers communicate in Bangla, English, and Banglish interchangeably and existing chatbot solutions fail to handle this mixed-script reality.

A production-grade, multi-tenant SaaS chatbot platform was built using LaBSE transfer learning for multilingual sentence embeddings, a ChromaDB-backed RAG pipeline for knowledge-grounded responses, a LangGraph StateGraph for multi-turn agent orchestration, and a FastAPI + React stack served end-to-end via Docker Compose.

The main finding is that a frozen pre-trained multilingual transformer (LaBSE) — without any domain-specific fine-tuning — is sufficient to power a semantically meaningful FAQ retrieval system across Bangla and English in a RAG setup. Combined with keyword-pattern intent routing for Banglish, the system correctly handles order tracking, product queries, complaint escalation, and multi-turn order placement without requiring labelled training data.

The prediction app is fully containerised: `docker compose up --build` launches the complete platform with the chat widget, admin panels, ecommerce storefront, and Prometheus metrics — ready to demonstrate the full workflow end-to-end.

Key learning from the project: multi-tenant data isolation at the vector store level (ChromaDB `tenant_id` metadata filter) is a clean and scalable pattern that avoids managing separate databases per customer while still keeping knowledge bases fully separated.

---

## Appendix

### A. Final Submission Checklist

- [x] Selected one approved project domain — **NLP Customer Support**
- [x] Public GitHub repository is accessible
- [x] Dataset is not committed to GitHub (`*.db`, `chroma_db/` gitignored)
- [x] Data is auto-generated on first run (no manual download needed)
- [x] Course techniques clearly documented — Transfer Learning, RAG, Transformer, NLP, Docker
- [x] Prediction app supports sample chat input
- [x] Prediction app served using Docker (`docker compose up --build`)
- [x] Report includes UI screenshots (Figures 1–6)
- [x] Limitations and future work documented
- [x] Deadline respected: submitted by **25 June 2026**

### B. Final Notes

This project is mandatory for certification. The certification program ends on **26 June 2026**, so the deadline of **25 June 2026** is strictly maintained.

There may be a project review on **26 June 2026**. Be ready to explain the LangGraph agent routing logic, the RAG pipeline (LaBSE → ChromaDB → LLM prompt construction), multi-tenant isolation via API key, the Docker setup, and the screenshots in this report.
