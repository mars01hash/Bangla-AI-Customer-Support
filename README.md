# Bangla AI Customer Support Platform

A production-grade, multi-tenant SaaS chatbot platform built for Bangladeshi ecommerce. Any ecommerce store can embed the AI-powered chat widget on their website, manage their own knowledge base, and route customer tickets to their support agents — all independently.

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
- **AI**: OpenAI GPT-4o-mini, LaBSE sentence embeddings
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

# Copy env file and add your OpenAI key
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

`backend/.env`:

```env
# Required for real AI responses
OPENAI_API_KEY=sk-proj-...

# Optional — Telegram bot
TELEGRAM_BOT_TOKEN=123456789:ABC-...

# Optional — override defaults
DATABASE_URL=sqlite:///./support_platform.db
LLM_PROVIDER=openai
JWT_SECRET=change-me-in-production
ADMIN_INITIAL_PASSWORD=adminpassword123
```

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
Language Detection → Sentiment Analysis
     │
     ▼
Router Node
  ├── greeting    → Greeting Node
  ├── faq         → FAQ Node (ChromaDB RAG, tenant-scoped)
  ├── order       → Order Node (SQLite lookup by order ID)
  ├── billing     → Billing Node (asks clarifying question first)
  ├── complaint   → Complaint Node (asks what went wrong first)
  └── escalation  → Escalation Node (creates support ticket)
```

**Clarification-first behaviour:** The bot asks a clarifying question before creating any support ticket. On the follow-up turn, it collects the user's details and then creates the ticket — producing more useful descriptions for agents.

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
│   │   │   ├── graph.py        # LangGraph StateGraph
│   │   │   ├── nodes.py        # All agent node implementations
│   │   │   └── state.py        # AgentState TypedDict (incl. tenant_id)
│   │   ├── api/
│   │   │   └── endpoints.py    # All FastAPI routes
│   │   ├── rag/
│   │   │   ├── vectorstore.py  # ChromaDB + in-memory fallback
│   │   │   ├── embedder.py     # LaBSE sentence embeddings
│   │   │   └── ingestion.py    # Document chunking + indexing
│   │   ├── auth.py             # JWT + API-key authentication + role guards
│   │   ├── models.py           # SQLAlchemy ORM (Tenant, User, Ticket, KnowledgeEntry…)
│   │   ├── schemas.py          # Pydantic request/response schemas
│   │   ├── database.py         # SQLAlchemy engine + session
│   │   ├── config.py           # Settings loaded from .env
│   │   └── main.py             # FastAPI app + DB schema init + seeding
│   ├── telegram_poll.py        # Telegram polling mode
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
│       │   └── ChatWidget.jsx      # Floating chat widget (auto-sends prefilled messages)
│       └── App.jsx                 # Role-based routing (super_admin/store_admin/agent/customer)
├── deployment/
│   └── docker-compose.yml
├── run.txt                         # Quick start reference card
└── README.md
```

---

## Key Design Decisions

**Multi-tenant via API key header** — Widget requests carry `X-Api-Key` instead of a user JWT. This means customers don't need to log in and each ecommerce site can self-serve without platform involvement.

**Tenant-scoped ChromaDB** — Knowledge base entries are indexed with `{"tenant_id": "..."}` metadata. The FAQ agent filters by this field, then falls back to the global collection. This avoids managing separate vector databases per tenant while still isolating content.

**Clarification before escalation** — The `_has_pending_clarification()` helper checks whether the last AI message was a question. If so, subsequent replies are routed directly to ticket creation rather than asking again. This prevents the bot from repeatedly asking the same question.

**Module-scope checkout components** — React re-mounts a component when its constructor reference changes between renders. Defining `CheckoutView` and `PaymentView` as inner functions of `EcommercePage` caused the form inputs to re-mount on every keystroke. Moving them to module scope (with their own local `useState`) fixed the input lag entirely.
