# Bangla AI Customer Support Platform

A production-grade, **multi-tenant SaaS chatbot platform** built for Bangladeshi ecommerce. Any ecommerce store can embed the AI-powered chat widget on their website, manage their own knowledge base, and route customer tickets to their support agents — all independently.

---

## What It Does

=== "For Customers"
    - Chat in **Bangla, English, or Banglish** (mixed script)
    - Ask about products, pricing, orders, delivery, and payments
    - Place orders directly through the chat — no form to fill out
    - Get instant answers from the store's knowledge base
    - Escalate to a human agent when needed

=== "For Store Admins"
    - Embed the chat widget on any website with a single `<script>` tag
    - Manage a per-store knowledge base (Q&A indexed in a vector store)
    - Invite support agents and assign them to your store
    - View and resolve customer tickets scoped to your store
    - Customise widget colour and welcome message

=== "For the Platform Owner"
    - Create and manage multiple store tenants from one dashboard
    - Rotate API keys per store
    - View cross-platform analytics and user management

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + LangGraph + SQLite / PostgreSQL |
| AI Agents | LangGraph StateGraph (8 specialised nodes) |
| Embeddings | LaBSE sentence-transformer (multilingual) |
| Vector Store | ChromaDB (tenant-scoped) |
| LLM | OpenAI / Groq / OpenRouter / HuggingFace (pluggable) |
| Frontend | React 18 + Vite + Tailwind CSS |
| Auth | JWT (users) + API key (widget) |
| Integrations | Telegram Bot, Prometheus metrics, Grafana |

---

## Quick Links

- [Local development setup](getting-started/local-dev.md)
- [Docker setup](getting-started/docker.md)
- [Agent workflow explained](architecture/agent-workflow.md)
- [How to embed the widget](user-guide/chat-widget.md)
- [Order placement flow](features/order-placement.md)
- [API reference](api-reference/public.md)
