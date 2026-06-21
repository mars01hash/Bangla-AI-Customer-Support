# Store Admin Endpoints

All endpoints require a JWT token with role `store_admin` (or `super_admin`).

**Auth header:**
```
Authorization: Bearer <jwt_token>
```

Get a token via `POST /api/auth/token` with your email and password.

---

## Store Settings

### `GET /api/my-store`
Returns the authenticated admin's store details.

### `PUT /api/my-store`
Update store name, welcome message, or widget colour.

**Request:**
```json
{
  "name": "ShopBD",
  "welcome_message": "স্বাগতম! কীভাবে সাহায্য করতে পারি?",
  "color": "#6366f1"
}
```

---

## Embed Code

### `GET /api/my-store/embed-code`
Returns the embed snippet and current API key.

**Response:**
```json
{
  "api_key": "sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "snippet": "<script>window.SHOPBOT_KEY=...</script>"
}
```

---

## Knowledge Base

### `GET /api/my-store/knowledge`
List all KB entries for this store.

### `POST /api/my-store/knowledge`
Add a new Q&A entry. Immediately indexed into ChromaDB.

**Request:**
```json
{
  "question": "ডেলিভারি কত দিনে হয়?",
  "answer": "ঢাকায় ২-৩ দিন, ঢাকার বাইরে ৪-৫ দিন।"
}
```

### `DELETE /api/my-store/knowledge/{id}`
Delete a KB entry and remove it from the vector store.

---

## Agents

### `GET /api/my-store/agents`
List all agents assigned to this store.

### `POST /api/my-store/agents`
Invite a new agent by email.

**Request:**
```json
{
  "email": "newagent@shopbd.com",
  "name": "Karim"
}
```

### `DELETE /api/my-store/agents/{user_id}`
Remove an agent from this store (does not delete the user account).

---

## Stats

### `GET /api/my-store/stats`
Returns aggregate stats for this store.

**Response:**
```json
{
  "total_tickets": 42,
  "open_tickets": 8,
  "total_conversations": 310,
  "kb_entries": 15,
  "agent_count": 2
}
```

---

## Tickets (Agent + Store Admin)

### `GET /api/tickets`
Returns tickets scoped to the authenticated user's store. Agents and store admins see the same filtered set.

**Query params:** `?status=open`, `?category=order`

### `PUT /api/tickets/{ticket_id}`
Update a ticket's status or assigned agent.

**Request:**
```json
{
  "status": "in_progress",
  "assigned_agent_id": 5
}
```
