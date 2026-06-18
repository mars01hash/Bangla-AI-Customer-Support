# System Architecture and Developer Guide

This document describes the technical architecture, LangGraph execution flows, and developer patterns of the Bangla Customer Support Platform.

---

## Processing Flow Lifecycle

When a message is received (via HTTP POST or WebSockets), the application routes it through the following pipeline:

```
[User Query]
    │
    ▼
[Language & Sentiment Detector]
    │  ├─ Detects: 'bn', 'en', 'mixed'
    │  └─ Classifies sentiment: 'positive', 'neutral', 'negative'
    ▼
[Intent Router Heuristic]
    │
    ├─► greeting   ──► [Greeting Agent]
    ├─► billing    ──► [Billing Agent]
    ├─► order      ──► [Order Agent]
    ├─► complaint  ──► [Complaint Agent] ──(if angry)──┐
    ├─► escalation ──► [Escalation Agent] ◄────────────┘
    └─► faq        ──► [Knowledge Retrieval Agent]
                            │
                      [ChromaDB RAG]
                            │
                      (Is confidence < 0.35?)
                            ├─► [Yes] ──► [Escalation Agent]
                            └─► [No]  ──► (Return Synthesized Citation)
```

---

## Component Details

### 1. LangGraph State Management

The core processing engine is driven by a compiled `StateGraph` using a typed state. The state keys track the conversation turn:

```python
class AgentState(TypedDict):
    messages: List[BaseMessage]   # Full chat history with append reducer
    current_message: str          # Current message to evaluate
    detected_language: str        # 'bn', 'en', 'mixed'
    detected_sentiment: str       # 'positive', 'neutral', 'negative'
    category: str                 # Intent category node identifier
    confidence_score: float       # RAG certainty [0.0 - 1.0]
    sources: List[Dict]           # Citations
    ticket_escalated: bool        # Escalation trigger flag
    ticket_id: Optional[str]      # DB Ticket primary key
    answer: str                   # Generated agent response
```

### 2. Multi-Lingual Semantic Search (RAG)

- **Embedder**: Generates a 768-dimensional dense vector representing the text using `SentenceTransformer('sentence-transformers/LaBSE')`. LaBSE (Language-Agnostic BERT Sentence Embedding) is selected specifically for its state-of-the-art capability in aligning Bangla, English, and transliterated Banglish (e.g. "order confirm hoyeche?") into a unified vector space.
- **ChromaDB**: Evaluates documents using cosine similarity. Distances are mapped to confidence ratings:
  $$\text{Confidence} = 1.0 - \text{Cosine Distance}$$
  A confidence score threshold of **0.35** is enforced. If a query matches no document above this threshold, it triggers automated routing to the `Escalation Agent`.

### 3. Session & Long-Term Memory

- **Turn Memory**: The FastAPI WebSocket loop (`/api/chat/ws/{session_id}`) loads the previous 10 database logs for a specific session code, compiles them into LangChain messages, and executes the graph.
- **Customer Profiles**: Conversations and tickets are tracked using the customer's email and user ID. When an issue escalates, the system queries past user sentiment records and open tickets to prioritize the queue.

---

## Developer Extension Guide

### Adding a New Specialist Agent Node
To register a new specialist (e.g., a "Refund Agent"):
1. **Define the Node**: Write a function in [nodes.py](file:///h:/nlp-customer-support-bangla/backend/app/agents/nodes.py) returning a partial state update:
   ```python
   def refund_agent_node(state: AgentState) -> Dict[str, Any]:
       # refund lookup logic
       return {"answer": "Refund request processed.", "messages": [AIMessage(content="...")]}
   ```
2. **Register the Node**: Add it to [graph.py](file:///h:/nlp-customer-support-bangla/backend/app/agents/graph.py):
   ```python
   builder.add_node("refund", refund_agent_node)
   ```
3. **Configure Routing**: Update the routing edge logic `route_from_detector` to direct keywords to the new node and define the transition to `END`.
