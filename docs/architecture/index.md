# System Overview

## Platform Architecture

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

## Request Flow

```
Customer types a message
        │
        ▼
   ChatWidget.jsx  (React)
        │  POST /api/chat  (or /api/widget/chat with X-Api-Key)
        ▼
   FastAPI endpoint
        │  resolves tenant from API key (widget) or session
        ▼
   LangGraph support_graph
        │  detector node → route
        ▼
   Agent node  (greeting / faq / product / order / order_placement / ...)
        │  optional LLM call + DB / ChromaDB lookup
        ▼
   AgentState  { answer, messages, ... }
        │
        ▼
   JSON response → ChatWidget renders answer
```

## Database Models

| Model | Key Fields |
|---|---|
| `Tenant` | `id`, `name`, `api_key`, `is_active` |
| `User` | `id`, `email`, `role`, `tenant_id` |
| `Product` | `id`, `name`, `name_bn`, `price`, `category`, `in_stock` |
| `Order` | `order_id`, `customer_name`, `status`, `items`, `total_amount` |
| `Ticket` | `ticket_id`, `category`, `priority`, `status`, `tenant_id`, `assigned_agent_id` |
| `KnowledgeEntry` | `id`, `question`, `answer`, `tenant_id` |

## Component Map

```
backend/app/
├── main.py          ← FastAPI app, DB init, seeding
├── config.py        ← Settings from .env
├── auth.py          ← JWT + API-key auth, role guards
├── models.py        ← SQLAlchemy ORM models
├── schemas.py       ← Pydantic schemas
├── database.py      ← Engine + session
├── agents/
│   ├── graph.py     ← StateGraph wiring
│   ├── nodes.py     ← All 8 agent node functions
│   └── state.py     ← AgentState TypedDict
├── rag/
│   ├── vectorstore.py  ← ChromaDB wrapper
│   ├── embedder.py     ← LaBSE embeddings
│   └── ingestion.py    ← Document chunking
└── api/
    └── endpoints.py    ← All FastAPI routes
```
