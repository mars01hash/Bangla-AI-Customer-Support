# System Architecture and Developer Guide

This document describes the technical architecture, LangGraph execution flows, and developer patterns of the Bangla Customer Support Platform.

---

## Processing Flow Lifecycle

When a message is received (via HTTP POST or WebSocket), it passes through the following pipeline:

```
[User Query]
    │
    ▼
[Language & Sentiment Detector]
    │  ├─ Language: 'bn' | 'en' | 'mixed'
    │  ├─ Sentiment: 'positive' | 'neutral' | 'negative'
    │  └─ Intent:   'greeting' | 'faq' | 'order' | 'billing' | 'complaint' | 'escalation'
    ▼
[Intent Router]
    │
    ├─► greeting   ──► [Greeting Agent] ──────────────────────────────► END
    ├─► billing    ──► [Billing Agent] ───────────────────────────────► END
    ├─► order      ──► [Order Agent] ─────────────────────────────────► END
    ├─► complaint  ──► [Complaint Agent]
    │                       │
    │               (sentiment == negative?)
    │                 ├─ Yes ──► [Escalation Agent] ──────────────────► END
    │                 └─ No  ──────────────────────────────────────────► END
    ├─► escalation ──► [Escalation Agent] ────────────────────────────► END
    └─► faq        ──► [Knowledge Retrieval Agent]
                            │
                     [ChromaDB RAG — avg confidence of top-3 matches]
                            │
                   (confidence < 0.35?)
                     ├─ Yes ──► [Escalation Agent] ──────────────────► END
                     └─ No  ──► (Return synthesised citation answer) ─► END
```

---

## Component Details

### 1. LangGraph State Management

The processing engine is a compiled `StateGraph` using a typed `AgentState`. Each node receives the full state and returns a **partial dict**; LangGraph merges it into the accumulated state — keys not returned retain their previous values.

```python
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]  # append reducer
    current_message: str          # raw input for this turn
    session_id: str               # client session identifier
    detected_language: str        # 'bn' | 'en' | 'mixed'
    detected_sentiment: str       # 'positive' | 'neutral' | 'negative'
    category: str                 # intent label used by routers
    confidence_score: float       # RAG retrieval certainty [0.0 – 1.0]
    sources: List[Dict]           # RAG citation list
    answer: str                   # final response string
    ticket_escalated: bool        # True when an auto-ticket is created
    ticket_id: Optional[str]      # e.g. "TKT-A8EC0BA9"
```

Routing functions (`route_from_detector`, `route_from_faq`, `route_from_complaint`) read `state["category"]` and return the next node label or `END`.

### 2. Multilingual Semantic Search (RAG)

- **Embedder** (`rag/embedder.py`): Generates 768-dimensional dense vectors using `SentenceTransformer('sentence-transformers/LaBSE')`. LaBSE aligns Bangla, English, and transliterated Banglish (e.g., "order confirm hoyeche?") into a shared vector space.
- **ChromaDB** (`rag/vectorstore.py`): Retrieves the top-3 nearest documents by cosine similarity. Distance is converted to a confidence score:
  $$\text{Confidence} = 1.0 - \text{Cosine Distance}$$
- **Threshold**: If the average confidence of retrieved documents is below **0.35**, the FAQ node returns `{"category": "escalation"}` and the graph reroutes to the Escalation Agent.
- **Confidence averaging**: Computed as a plain Python mean — `sum(scores) / len(scores)` — with an empty-list guard (`else 0.0`).

### 3. LLM Integration (`agents/nodes.py`)

`query_llm_api()` is a synchronous helper that dispatches to the configured provider:

| `LLM_PROVIDER` value | Target |
|---|---|
| `mock` | Returns `""` immediately; nodes use heuristic fallbacks |
| `openai` | `https://api.openai.com/v1/chat/completions` |
| `groq` | `https://api.groq.com/openai/v1/chat/completions` |
| `huggingface` | `https://api-inference.huggingface.co/models/<model>` |

Non-200 responses from all providers are logged at `ERROR` level (status code + first 200 chars of the body) before falling back to heuristic responses. Network-level errors are caught and also logged.

Because `httpx.post()` is synchronous, it **must not be called directly from the async WebSocket handler**. The WebSocket endpoint wraps the graph invocation in `asyncio.get_event_loop().run_in_executor(None, support_graph.invoke, state_input)` to keep blocking I/O off the event loop. The REST `/api/chat` endpoint is a synchronous `def` route and runs in FastAPI's thread pool automatically.

### 4. Session Memory and History Loading

Both the REST and WebSocket chat handlers load the last 10 messages for the session using a **SQL-side LIMIT query** rather than a Python slice:

```python
recent_msgs = (
    db.query(Message)
    .filter(Message.conversation_id == conv.id)
    .order_by(Message.id.desc())
    .limit(10)
    .all()
)
history = [HumanMessage(content=m.content) if m.sender == "user"
           else AIMessage(content=m.content)
           for m in reversed(recent_msgs)]
```

This avoids the ORM lazy-loading the full message table before slicing in Python, keeping memory usage constant regardless of conversation length.

### 5. Voice Processing

- **STT** (`/api/voice/stt`): Accepts a WAV upload. If `speech_recognition` is installed, it attempts Google STT with `bn-BD` first, then `en-US`. Falls back to a mock string when the library is unavailable or recognition fails. **No authentication required** — this endpoint is accessible from the public customer chat.
- **TTS** (`/api/voice/tts`): Converts text to MP3 using `gTTS`. Maps `lang="bn"` and `lang="mixed"` to Google's `"bn"` locale. Returns a silent MP3 stub on failure. **No authentication required.**

The React frontend uses `MediaRecorder` to capture real 2-second microphone clips before POSTing to the STT endpoint.

### 6. Auto-Escalation Ticket Creation

When the Escalation Agent fires, it:
1. Generates a unique ticket ID: `TKT-{uuid4().hex[:8].upper()}`.
2. Queries the `User` table for the first available agent and assigns the ticket.
3. Sets priority to `"high"` for negative-sentiment messages, `"medium"` otherwise.
4. Returns a confirmation message including the ticket ID to the customer.

> **Known limitation:** Auto-escalation tickets are created with a placeholder `customer_name` and `email` because the `/api/chat` endpoint does not require authentication. To associate tickets with real customers, integrate authentication into the chat flow.

---

## Developer Extension Guide

### Adding a New Specialist Agent Node

1. **Define the node** in `backend/app/agents/nodes.py`:
   ```python
   def refund_agent_node(state: AgentState) -> Dict[str, Any]:
       # lookup refund logic...
       return {
           "answer": "Your refund has been initiated.",
           "confidence_score": 0.95,
           "sources": [],
           "messages": [AIMessage(content="Your refund has been initiated.")]
       }
   ```

2. **Register the node** in `backend/app/agents/graph.py`:
   ```python
   from app.agents.nodes import refund_agent_node
   builder.add_node("refund", refund_agent_node)
   builder.add_edge("refund", END)
   ```

3. **Add a keyword trigger** in `classify_intent_heuristics()` (`nodes.py`):
   ```python
   refund_words = ["ফেরত", "রিফান্ড", "refund", "return", "money back"]
   for word in refund_words:
       if word in text_lower:
           return "refund"
   ```

4. **Wire the routing edge** in `route_from_detector()` (`graph.py`):
   ```python
   if category in ["greeting", "faq", "order", "billing", "complaint", "escalation", "refund"]:
       return category
   ```
   And add `"refund": "refund"` to the `add_conditional_edges` map.

### Adding a New Knowledge Document

Upload via the admin dashboard or directly via the API:
```bash
curl -X POST http://localhost:8090/api/upload \
  -H "Authorization: Bearer <admin-jwt>" \
  -F "file=@faq_guide.pdf"
```

The ingestion pipeline chunks the file with overlapping paragraphs, embeds each chunk with LaBSE, and stores the vectors in ChromaDB.
