# Agent Workflow

The AI layer is a **LangGraph StateGraph** — a directed graph of specialised nodes. Every customer message enters the graph at the `detector` node, which classifies intent and routes to the appropriate agent.

## Graph Structure

```
User Message
     │
     ▼
[detector]  — language + sentiment + intent classification
     │
     ├──► [greeting]        → END
     ├──► [faq]             → END  (or → [escalation] if low confidence)
     ├──► [product]         → END
     ├──► [order]           → END  (order status lookup)
     ├──► [order_placement] → END  (multi-turn order collection)
     ├──► [billing]         → END
     ├──► [complaint]       → END  (or → [escalation])
     └──► [escalation]      → END  (creates support ticket)
```

## Node Descriptions

### `detector`
Runs on every message. Detects:

- **Language** — Bangla (`bn`), English (`en`), or mixed (`mixed`) by scanning Unicode blocks
- **Sentiment** — `positive`, `negative`, or `neutral` using keyword lists
- **Category** — one of `greeting`, `faq`, `product`, `order`, `order_placement`, `billing`, `complaint`, `escalation`

Intent classification uses a priority chain:

1. Mid-escalation continuation check
2. Mid-order-collection check (bot already asked for name/mobile/address)
3. Explicit buy intent keywords (English, Bangla, Banglish)
4. Affirmative response to a bot order offer
5. Heuristic keyword match against category word lists

### `faq`
Queries ChromaDB with LaBSE embeddings, filtered by `tenant_id`. Falls back to the global collection if no tenant match. Passes retrieved context + product catalog + conversation history to the LLM.

### `product`
Handles five sub-intents with dedicated prompts:

| Sub-intent | Trigger keywords |
|---|---|
| Comparison | `compare`, `vs`, `তুলনা`, `পার্থক্য` |
| Budget search | `under`, `within`, `বাজেট`, `সস্তা` |
| Recommendation | `best`, `suggest`, `সেরা`, `পরামর্শ` |
| Catalog browse | `show me`, `list`, `কী আছে`, `দেখান` |
| Specific product | product name found in message |

### `order`
Looks up an existing order by ID (`ORD-XXXXX` or `#XXXXX`). If no ID is present, asks the customer politely. Also searches recent message history for a previously mentioned ID.

### `order_placement`
Multi-turn node that collects name → mobile → address, then creates an `Order` row and a staff `Ticket` in the database. See [Order Placement Flow](../features/order-placement.md) for full details.

### `billing`
Answers questions about payment methods (bKash, Nagad, Rocket, Visa/Mastercard, COD) and refund policy (7-day returns, 3-5 working days).

### `complaint`
Asks one clarifying question before escalating. On the follow-up turn, `_has_pending_clarification()` returns `True` and the message is re-routed to `escalation`.

### `escalation`
Two-turn behaviour:

1. **First visit** — asks 1-2 clarifying questions; does NOT create a ticket yet
2. **Second visit** (after clarification) — creates a `Ticket` in the database with conversation summary, assigns to an available agent, responds with the ticket ID

## State Schema

```python
class AgentState(TypedDict):
    current_message: str
    messages: list                # full conversation history (LangChain messages)
    detected_language: str        # "bn" | "en" | "mixed"
    detected_sentiment: str       # "positive" | "negative" | "neutral"
    category: str                 # routing category
    answer: str                   # node output
    confidence_score: float
    sources: list
    ticket_escalated: bool
    ticket_id: str | None
    tenant_id: str | None         # resolved from X-Api-Key header
    preferred_language: str | None  # explicit language toggle from UI
```
