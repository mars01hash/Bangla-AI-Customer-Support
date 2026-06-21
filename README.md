# Bangla AI Customer Support Platform

A production-grade, multi-tenant SaaS chatbot platform built for Bangladeshi ecommerce. Any ecommerce store can embed the AI-powered chat widget on their website, manage their own knowledge base, and route customer tickets to their support agents — all independently.

---

## Screenshots

### Chat Widget — Bangla & English Support
![Chat Widget](screenshots/chat_widget.png)

### Customer Chat — Order Tracking
![Order Tracking](screenshots/order_tracking.png)

### Store Admin Panel — Knowledge Base Management
![Store Admin Panel](screenshots/store_admin_panel.png)

### Agent Dashboard — Ticket Queue
![Agent Dashboard](screenshots/agent_dashboard.png)

### Super Admin Panel — Tenant Management
![Super Admin Panel](screenshots/super_admin_panel.png)

### ShopBD Ecommerce Storefront
![Ecommerce Storefront](screenshots/ecommerce_storefront.png)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   PLATFORM LAYER                            │
│  Super Admin — manages all stores, all users, API keys      │
└────────────────────────┬────────────────────────────────────┘
                         │ creates
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌─────────┐     ┌─────────┐     ┌─────────┐
    │ ShopBD  │     │FashionBD│     │  Any    │
    │ Tenant  │     │ Tenant  │     │  Store  │
    └────┬────┘     └────┬────┘     └────┬────┘
         │               │               │
    Store Admin      Store Admin    Store Admin
    (KB, agents,     (KB, agents,   (KB, agents,
     embed code)      embed code)    embed code)
         │
    ┌────┴────┐
    │ Agents  │  ← handle tickets for their store only
    └─────────┘
         │
    Customers  ← anonymous users via embedded widget
```

**Tech stack:**
- **Backend**: FastAPI + LangGraph + ChromaDB + SQLite/PostgreSQL
- **Frontend**: React 18 + Vite + Tailwind CSS
- **AI**: OpenAI / Groq / OpenRouter / HuggingFace LLMs + LaBSE sentence embeddings
- **Integrations**: Telegram Bot, Prometheus metrics

---

## User Roles & Access

| Role | What they can do |
|---|---|
| `super_admin` | Create/manage all tenants; view all users, tickets, analytics; rotate API keys |
| `store_admin` | Manage their store's knowledge base, agents, widget settings, and embed code; view their store's tickets |
| `agent` | View and update support tickets for their assigned store only |
| `customer` | Use the chat widget — no login required |

---

## Quick Start

### Option A — Local Development

**1. Backend (FastAPI)**

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt

# Copy env file and configure your LLM provider
cp .env.example .env

uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload
```

API: `http://localhost:8090`  
Swagger docs: `http://localhost:8090/docs`

**2. Frontend (React + Vite)**

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:5173`

---

### Option B — Docker (Full Stack)

```bash
cd deployment
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost |
| API Swagger | http://localhost:8090/docs |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (admin / admin) |

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in your values:

```env
# ── LLM Provider ──────────────────────────────────────────────────────────────
# Options: mock | openai | groq | huggingface | openrouter
LLM_PROVIDER=openrouter
LLM_API_KEY=sk-or-v1-...

# Model name depends on provider:
#   openai:     gpt-4o-mini
#   groq:       llama-3.3-70b-versatile
#   openrouter: nvidia/nemotron-3-super-120b-a12b:free
LLM_MODEL_NAME=nvidia/nemotron-3-super-120b-a12b:free

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL=sqlite:///./support_platform.db
# DATABASE_URL=postgresql://user:password@localhost:5432/support_db

# ── Vector Store ──────────────────────────────────────────────────────────────
CHROMA_PERSIST_DIRECTORY=./chroma_db

# ── Auth ──────────────────────────────────────────────────────────────────────
JWT_SECRET=change-me-in-production

# ── Telegram Bot (optional) ───────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN=
```

**LLM provider notes:**
- `mock` — no API key needed; returns empty strings (heuristic fallbacks kick in)
- `openai` — set `LLM_API_KEY` to your `sk-proj-...` key
- `groq` — free tier available at console.groq.com
- `openrouter` — free models available (e.g. `nvidia/nemotron-3-super-120b-a12b:free`)
- `huggingface` — set `LLM_API_KEY` to your HF token

---

## Pre-seeded Demo Accounts

| Role | Email | Password | Notes |
|---|---|---|---|
| Super Admin | `super@platform.com` | `superpassword123` | Full platform access |
| Store Admin | `admin@shopbd.com` | `storepassword123` | ShopBD tenant |
| Store Admin | `admin@fashionbd.com` | `storepassword123` | FashionBD tenant |
| Agent | `agent@shopbd.com` | `agentpassword123` | ShopBD tickets only |
| Legacy Admin | `admin@example.com` | `adminpassword123` | super_admin alias |
| Legacy Agent | `agent@example.com` | `agentpassword123` | ShopBD tickets |

---

## Portal Navigation

Login auto-routes to the correct dashboard based on role:

### Super Admin Panel (`/superadmin`)
- View and manage all registered store tenants
- Create new tenants (generates unique API key automatically)
- Activate / deactivate stores
- Rotate API keys (invalidates the old one instantly)
- View all platform users with their roles and store assignments

### Store Admin Panel (`/storeadmin`) — 6 tabs

| Tab | What it does |
|---|---|
| **Overview** | Stats (tickets, conversations, KB entries, agents) + quick-start checklist |
| **Knowledge Base** | Add/delete Q&A entries — indexed into vector store per tenant |
| **Embed Code** | Copy the HTML snippet to paste into your website |
| **Agents** | Invite support agents (auto-assigned to this store), remove agents |
| **Tickets** | View and update customer tickets scoped to this store |
| **Settings** | Widget color picker + welcome message editor |

### Agent Dashboard (`/dashboard`)
- Ticket queue filtered to their store
- Analytics charts
- Order management
- Knowledge document upload (global KB, super_admin only)

---

## Embedding the Widget on Any Website

Store admins copy their embed snippet from the **Embed Code** tab:

```html
<!-- Paste before </body> on your website -->
<script>
  window.SHOPBOT_KEY   = "sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
  window.SHOPBOT_API   = "https://your-platform-domain.com";
  window.SHOPBOT_COLOR = "#6366f1";
</script>
<script src="https://your-platform-domain.com/api/widget.js" async></script>
```

**How tenant isolation works:**
1. Widget sends `X-Api-Key` header with every chat request
2. Backend resolves the tenant from the API key
3. FAQ agent queries ChromaDB filtered by `tenant_id`
4. Falls back to global knowledge base if no tenant-specific match
5. Support tickets are tagged with the tenant — agents see only their store's tickets

---

## Agent Workflow (LangGraph)

```
User Message
     │
     ▼
Language & Sentiment Detection
     │
     ▼
Router Node
  ├── greeting        → Greeting Node
  ├── faq             → FAQ Node (ChromaDB RAG, tenant-scoped)
  │                         └── [low confidence] → Escalation Node
  ├── product         → Product Node (compare, recommend, browse, lookup)
  ├── order           → Order Status Node (DB lookup by order ID)
  ├── order_placement → Order Placement Node (multi-turn: collects details → creates order)
  ├── billing         → Billing Node
  ├── complaint       → Complaint Node → Escalation Node
  └── escalation      → Escalation Node (creates support ticket)
```

**Buy intent detection** — The router recognises purchase intent across English, Bangla, and Banglish:
- English: `"i want to buy"`, `"order now"`, `"place order"`, …
- Bangla: `"কিনতে চাই"`, `"অর্ডার করতে চাই"`, `"নিতে চাই"`, …
- Banglish: `"order korbo"`, `"kinbo"`, `"order debo"`, …

**Order placement flow (multi-turn):**
1. Customer expresses buy intent → routed to `order_placement`
2. Bot asks for full name → mobile number → delivery address (one field per turn)
3. On completion, an `Order` row and a staff `Ticket` are created in the database
4. Bot confirms with the generated Order ID

**Clarification-first behaviour** — The bot asks a clarifying question before creating any support ticket. On the follow-up turn it collects the user's details and creates the ticket, producing more useful descriptions for agents.

**Language options** — The chat widget includes a language toggle (Bangla / English). The selected language is passed as `preferred_language` through the agent state and respected by every node's response.

---

## Ecommerce Storefront (ShopBD Demo)

A full Bangladeshi ecommerce demo is built in — it shows the bot integrated into a real shopping flow:

- **Browse** — 12 products across fashion, electronics, accessories, shoes
- **Cart** — add/remove items, quantity controls
- **Checkout** — name, phone, address, delivery method (standard/express)
- **Payment** — bKash, Nagad (phone + OTP), Card (16-digit + expiry + CVV), Cash on Delivery
- **Order tracking** — orders saved to SQLite; customers can ask the chatbot about their order
- **"Track in Chat"** button — pre-fills the chatbot with the order ID and auto-sends

---

## API Reference

### Public (no auth required)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/chat` | Main chat (session-based) |
| `POST` | `/api/widget/chat` | Widget chat (`X-Api-Key` header) |
| `GET` | `/api/widget/config` | Widget branding for a store |
| `POST` | `/api/orders/place` | Place an ecommerce order |
| `GET` | `/api/orders/track/{id}` | Track order status |
| `POST` | `/api/feedback` | Submit chat rating |

### Store Admin (JWT, role: store_admin)

| Method | Path | Description |
|---|---|---|
| `GET/PUT` | `/api/my-store` | Get or update store settings |
| `GET` | `/api/my-store/embed-code` | Get embed snippet + API key |
| `GET/POST` | `/api/my-store/knowledge` | List / add KB entries |
| `DELETE` | `/api/my-store/knowledge/{id}` | Delete a KB entry |
| `GET/POST` | `/api/my-store/agents` | List / invite agents |
| `DELETE` | `/api/my-store/agents/{id}` | Remove an agent |
| `GET` | `/api/my-store/stats` | Store-level analytics |

### Agent + Store Admin (JWT)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/tickets` | Tickets (scoped to your store) |
| `PUT` | `/api/tickets/{id}` | Update ticket status / assign agent |

### Super Admin only (JWT, role: super_admin)

| Method | Path | Description |
|---|---|---|
| `GET/POST` | `/api/tenants` | List / create tenants |
| `GET/PUT/DELETE` | `/api/tenants/{id}` | Manage a specific tenant |
| `POST` | `/api/tenants/{id}/rotate-key` | Rotate API key |
| `GET` | `/api/tenants/{id}/stats` | Per-tenant analytics |
| `GET` | `/api/users` | All platform users |
| `PUT` | `/api/users/{id}` | Update any user's role/tenant |

---

## Telegram Bot Setup

**Step 1 — Create a bot**
- Open Telegram → `@BotFather` → `/newbot`
- Copy the token → add to `backend/.env` as `TELEGRAM_BOT_TOKEN`

**Step 2 — Choose a mode**

*Polling (localhost, no public URL):*
```bash
cd backend && venv\Scripts\activate
python telegram_poll.py
```

*Webhook (production VPS / ngrok):*
```bash
curl -X POST https://yourdomain.com/api/telegram/set-webhook \
  -H "Authorization: Bearer <super_admin_jwt>" \
  -d "webhook_url=https://yourdomain.com/api/telegram/webhook"
```

> Do not run polling and webhook simultaneously for the same bot token.

---

## Project Structure

```
nlp-customer-support-bangla/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── graph.py        # LangGraph StateGraph + routing edges
│   │   │   ├── nodes.py        # All agent node implementations
│   │   │   └── state.py        # AgentState TypedDict (incl. tenant_id, preferred_language)
│   │   ├── api/
│   │   │   └── endpoints.py    # All FastAPI routes
│   │   ├── rag/
│   │   │   ├── vectorstore.py  # ChromaDB + in-memory fallback
│   │   │   ├── embedder.py     # LaBSE sentence embeddings
│   │   │   └── ingestion.py    # Document chunking + indexing
│   │   ├── auth.py             # JWT + API-key authentication + role guards
│   │   ├── models.py           # SQLAlchemy ORM (Tenant, User, Ticket, Order, Product…)
│   │   ├── schemas.py          # Pydantic request/response schemas
│   │   ├── database.py         # SQLAlchemy engine + session
│   │   ├── config.py           # Settings loaded from .env
│   │   └── main.py             # FastAPI app + DB schema init + seeding
│   ├── telegram_poll.py        # Telegram polling mode
│   ├── .env.example            # Environment variable template
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── EcommercePage.jsx   # ShopBD storefront (browse→cart→checkout→payment→success)
│       │   ├── SuperAdminPanel.jsx # Platform owner dashboard
│       │   ├── StoreAdminPanel.jsx # Store admin (KB, embed, agents, tickets, settings)
│       │   ├── Dashboard.jsx       # Agent ticket + analytics dashboard
│       │   ├── CustomerChat.jsx    # Standalone chat demo
│       │   └── Login.jsx           # Multi-role login with one-click demo shortcuts
│       ├── components/
│       │   └── ChatWidget.jsx      # Floating chat widget (language toggle, auto-send)
│       └── App.jsx                 # Role-based routing (super_admin/store_admin/agent/customer)
├── deployment/
│   └── docker-compose.yml
├── .env.example                    # Root-level env reference
└── README.md
```

---

## Key Design Decisions

**Multi-tenant via API key header** — Widget requests carry `X-Api-Key` instead of a user JWT. This means customers don't need to log in and each ecommerce site can self-serve without platform involvement.

**Tenant-scoped ChromaDB** — Knowledge base entries are indexed with `{"tenant_id": "..."}` metadata. The FAQ agent filters by this field, then falls back to the global collection. This avoids managing separate vector databases per tenant while still isolating content.

**Order placement via multi-turn collection** — When buy intent is detected the bot enters a dedicated `order_placement` node that tracks which fields (name / mobile / address) have already been collected by inspecting message history. This keeps the node stateless — no server-side session needed.

**Banglish intent recognition** — Bangladeshi users frequently mix English words with Bangla grammar (e.g. "order korbo", "kinbo"). Affirmative and buy-intent checks include Banglish patterns so the router handles mixed-script input without needing an LLM call.

**Clarification before escalation** — The `_has_pending_clarification()` helper checks whether the last AI message was a question. If so, subsequent replies are routed directly to ticket creation rather than asking again. This prevents the bot from repeatedly asking the same question.

**Provider-agnostic LLM layer** — `query_llm_api()` in `nodes.py` supports OpenAI, Groq, OpenRouter, and HuggingFace behind a single interface. Setting `LLM_PROVIDER=mock` disables all external calls, making local development and testing cost-free.

**Module-scope checkout components** — React re-mounts a component when its constructor reference changes between renders. Defining `CheckoutView` and `PaymentView` as inner functions of `EcommercePage` caused form inputs to re-mount on every keystroke. Moving them to module scope (with their own local `useState`) fixed the input lag entirely.
