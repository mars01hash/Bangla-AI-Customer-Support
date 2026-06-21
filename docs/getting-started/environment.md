# Environment Variables

Copy `backend/.env.example` to `backend/.env` and set the values below.

## LLM Provider

```env
LLM_PROVIDER=openrouter
LLM_API_KEY=sk-or-v1-...
LLM_MODEL_NAME=nvidia/nemotron-3-super-120b-a12b:free
```

| `LLM_PROVIDER` | `LLM_API_KEY` | Recommended `LLM_MODEL_NAME` |
|---|---|---|
| `mock` | *(not needed)* | *(not needed)* |
| `openai` | `sk-proj-...` | `gpt-4o-mini` |
| `groq` | Groq console key | `llama-3.3-70b-versatile` |
| `openrouter` | `sk-or-v1-...` | `nvidia/nemotron-3-super-120b-a12b:free` |
| `huggingface` | HF token | Any HF inference model ID |

!!! tip "Free tier"
    `openrouter` with a `:free` model and `groq` both have generous free tiers — good for development without spending money.

!!! note "mock mode"
    Setting `LLM_PROVIDER=mock` disables all external LLM calls. The agent nodes fall back to heuristic responses. Useful for offline development and testing.

## Database

```env
# SQLite — works out of the box, no setup needed
DATABASE_URL=sqlite:///./support_platform.db

# PostgreSQL — for production
# DATABASE_URL=postgresql://user:password@localhost:5432/support_db
```

## Vector Store

```env
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

ChromaDB stores embeddings here. Delete this directory to reset the vector store and re-seed FAQs on next startup.

## Auth

```env
JWT_SECRET=change-me-in-production
```

!!! warning "Change in production"
    Use a long random string (at least 32 characters) for `JWT_SECRET` in any non-local environment.

## Telegram (Optional)

```env
TELEGRAM_BOT_TOKEN=123456789:ABC-...
```

Leave blank to disable the Telegram integration. See [Telegram Bot](../features/telegram.md) for setup instructions.
