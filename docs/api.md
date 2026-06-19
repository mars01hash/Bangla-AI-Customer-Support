# API Reference

Full request/response documentation for the platform's REST and WebSocket interfaces.

---

## Base URL

| Environment        | URL                                    |
|--------------------|----------------------------------------|
| Local development  | `http://localhost:8090`                |
| Docker Compose     | `http://localhost:8090`                |
| Kubernetes ingress | `http://support.bangla-ai.local/api`   |

Interactive Swagger UI: `http://localhost:8090/docs`

---

## Authentication

Protected routes require a JWT bearer token in the `Authorization` header:

```
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

Tokens are obtained from `POST /api/auth/token` and expire after 60 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).

**Endpoints that do NOT require authentication:** `/api/chat`, `/api/chat/ws/{id}`, `/api/feedback`, `/api/voice/stt`, `/api/voice/tts`, `/api/metrics`.

---

## 1. Authentication

### Register User
`POST /api/auth/register`

```json
// Request body (JSON)
{
  "email": "customer@example.com",
  "password": "customerpassword123",
  "full_name": "Tahmid Hasan",
  "role": "customer"
}
```
`role` accepts: `"customer"` (default), `"agent"`, `"admin"`.

```json
// 200 OK
{
  "id": 3,
  "email": "customer@example.com",
  "full_name": "Tahmid Hasan",
  "role": "customer",
  "is_active": true,
  "created_at": "2026-06-19T10:00:00Z"
}
```

---

### Login — Obtain Token
`POST /api/auth/token`

Form-encoded body (OAuth2 password flow):
- `username`: user's email address
- `password`: account password

```json
// 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer",
  "role": "agent"
}
```

---

### Get Current User
`GET /api/auth/me` — requires Bearer token

```json
// 200 OK
{
  "id": 2,
  "email": "agent@example.com",
  "full_name": "Agent Rahat",
  "role": "agent",
  "is_active": true,
  "created_at": "2026-06-19T09:00:00Z"
}
```

---

## 2. Chat

### REST Chat Turn
`POST /api/chat` — no auth required

Multipart form fields:
- `message_in` — the customer's message (Bangla, English, or mixed)
- `session_id` — unique string identifying the conversation (e.g. `"session-abc123"`)

```json
// 200 OK
{
  "answer": "I have successfully tracked your order #12345. It is currently in transit and is expected to arrive within 2 business days.",
  "confidence_score": 0.9,
  "sources": [],
  "language": "en",
  "sentiment": "neutral",
  "ticket_escalated": false,
  "ticket_id": null
}
```

When a ticket is auto-created (low RAG confidence or negative complaint sentiment):
```json
{
  "answer": "I apologize that I couldn't resolve this automatically. I have created a priority support ticket (Ticket ID: TKT-A8EC0BA9). A human agent will follow up via email shortly.",
  "confidence_score": 1.0,
  "sources": [],
  "language": "en",
  "sentiment": "negative",
  "ticket_escalated": true,
  "ticket_id": "TKT-A8EC0BA9"
}
```

When the FAQ agent finds relevant documents, `sources` contains citation objects:
```json
{
  "sources": [
    {
      "id": "doc-uuid",
      "source": "faq_guide.pdf",
      "confidence": 0.82,
      "snippet": "Delivery within Dhaka takes 2–3 business days..."
    }
  ]
}
```

---

### WebSocket Chat
`WS /api/chat/ws/{session_id}` — no auth required

The server maintains conversation history for the session. Send JSON frames:

```json
// Client → Server
{ "message": "আমার বিলিং পেজ কাজ করছে না।" }
```

```json
// Server → Client
{
  "answer": "আমি দুঃখিত যে স্বয়ংক্রিয়ভাবে সমাধান করতে পারছি না। টিকিট তৈরি হয়েছে (TKT-B2F10C)।",
  "confidence_score": 1.0,
  "sources": [],
  "language": "bn",
  "sentiment": "negative",
  "ticket_escalated": true,
  "ticket_id": "TKT-B2F10C"
}
```

The WebSocket handler invokes the LangGraph workflow off the event loop (via `run_in_executor`) so concurrent sessions are not blocked during LLM calls.

---

## 3. Ticket Management

### Create Support Ticket
`POST /api/tickets` — no auth required

```json
// Request body (JSON)
{
  "customer_name": "Rahim Uddin",
  "email": "rahim@example.com",
  "category": "billing",
  "description": "Double charged on transaction #1002.",
  "priority": "medium"
}
```

`category` accepts: `"billing"`, `"order"`, `"complaint"`, `"escalation"`, `"general"`.
`priority` accepts: `"low"`, `"medium"`, `"high"`, `"urgent"`. If the description text contains negative sentiment keywords, priority is automatically upgraded to `"urgent"`.

```json
// 201 Created
{
  "id": 1,
  "ticket_id": "TKT-31A8B2",
  "customer_name": "Rahim Uddin",
  "email": "rahim@example.com",
  "category": "billing",
  "priority": "urgent",
  "status": "open",
  "description": "Double charged on transaction #1002.",
  "sentiment": "negative",
  "assigned_agent_id": null,
  "created_at": "2026-06-19T10:10:00Z",
  "updated_at": "2026-06-19T10:10:00Z"
}
```

---

### List Tickets
`GET /api/tickets` — requires Agent or Admin token

Optional query parameters:
- `status` — filter by `"open"`, `"in_progress"`, `"resolved"`, `"closed"`
- `priority` — filter by `"low"`, `"medium"`, `"high"`, `"urgent"`

Returns an array of ticket objects ordered by `created_at` descending.

---

### Update Ticket
`PUT /api/tickets/{ticket_id}` — requires Agent or Admin token

```json
// Request body (JSON) — all fields optional
{
  "status": "resolved",
  "priority": "low",
  "assigned_agent_id": 2
}
```

Returns the updated ticket object.

---

## 4. Feedback

### Submit Rating
`POST /api/feedback` — no auth required

```json
// Request body (JSON)
{
  "session_id": "session-abc123",
  "rating": 5,
  "comment": "Very helpful!"
}
```

`rating` is an integer from 1 (poor) to 5 (excellent). The `session_id` must correspond to an existing conversation; a 404 is returned otherwise.

```json
// 200 OK
{
  "id": 1,
  "conversation_id": 3,
  "rating": 5,
  "comment": "Very helpful!",
  "created_at": "2026-06-19T10:15:00Z"
}
```

---

## 5. Knowledge Base

### Upload Knowledge File
`POST /api/upload` — requires Admin token

Multipart form field:
- `file` — PDF, DOCX, CSV, or TXT document

The pipeline chunks the file with overlapping paragraphs, embeds each chunk with `LaBSE`, and stores vectors in ChromaDB.

```json
// 200 OK
{
  "message": "File uploaded and processed successfully",
  "filename": "faq_guide.pdf",
  "chunks_created": 34,
  "document_id": 1
}
```

---

## 6. Analytics

### Summary KPIs
`GET /api/analytics/summary` — requires Admin token

```json
// 200 OK
{
  "total_conversations": 128,
  "total_tickets": 24,
  "avg_response_time_seconds": 1.45,
  "resolution_rate": 0.75,
  "user_satisfaction_avg": 4.2,
  "frequent_faqs": [
    { "question": "অর্ডার ডেলিভারিতে কত সময় লাগবে?", "count": 25 }
  ],
  "sentiment_distribution": { "positive": 60, "neutral": 40, "negative": 28 },
  "language_distribution": { "bn": 80, "en": 30, "mixed": 18 }
}
```

---

### Chart Data
`GET /api/analytics/charts` — requires Admin token

```json
// 200 OK
{
  "daily_stats": [
    { "date": "2026-06-13", "conversations": 15, "tickets": 2, "feedback_avg": 4.0 },
    { "date": "2026-06-19", "conversations": 21, "tickets": 4, "feedback_avg": 4.5 }
  ],
  "sentiment_data": [
    { "name": "Positive", "value": 45, "color": "#10B981" },
    { "name": "Neutral",  "value": 30, "color": "#F59E0B" },
    { "name": "Negative", "value": 25, "color": "#EF4444" }
  ],
  "language_data": [
    { "name": "Bangla",           "value": 55, "color": "#3B82F6" },
    { "name": "English",          "value": 25, "color": "#8B5CF6" },
    { "name": "Mixed (Banglish)", "value": 20, "color": "#EC4899" }
  ]
}
```

---

## 7. Voice

### Speech-to-Text
`POST /api/voice/stt` — **no auth required**

Multipart form field:
- `file` — WAV audio file recorded from the browser's `MediaRecorder` API

Attempts Google STT with `bn-BD` locale first, then falls back to `en-US`. Returns a mock string when `speech_recognition` is not installed or recognition fails.

```json
// 200 OK — live transcription
{ "transcription": "আমার অর্ডার কোথায়?", "status": "success" }

// 200 OK — fallback mock
{ "transcription": "আমার বিলিং সমস্যা আছে এবং টিকিট খুলতে চাই।", "status": "mocked_success" }
```

---

### Text-to-Speech
`POST /api/voice/tts` — **no auth required**

Form fields:
- `text` — the text to synthesise
- `lang` — `"bn"` (default), `"en"`, or `"mixed"` (`"bn"` and `"mixed"` map to Google's Bangla locale)

Returns a streaming `audio/mp3` response. On gTTS failure, returns a short silent MP3 so the caller is not left with an empty body.

---

## 8. Telemetry

### Prometheus Metrics
`GET /api/metrics` — no auth required

Returns `text/plain` Prometheus exposition format. Scraped automatically by the Prometheus container in the Docker Compose stack.
