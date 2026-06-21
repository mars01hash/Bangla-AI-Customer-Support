# Multi-Tenant Design

## How Tenants Are Isolated

### API Key Authentication
Widget requests carry an `X-Api-Key` header instead of a user JWT. The backend resolves the tenant from this key on every request. Customers never need to log in, and each store is self-contained.

```
Widget (store A)  →  X-Api-Key: sk_aaa...  →  tenant_id = "shopbd"
Widget (store B)  →  X-Api-Key: sk_bbb...  →  tenant_id = "fashionbd"
```

### Tenant-Scoped Vector Store
Knowledge base entries are indexed into ChromaDB with `{"tenant_id": "..."}` metadata:

```python
# Store-admin adds a KB entry  →  indexed with tenant filter
vector_store.add_document(content, metadata={"tenant_id": "shopbd"})

# FAQ agent queries with filter first, falls back to global
results = vector_store.query(query, metadata_filter={"tenant_id": "shopbd"})
if not results:
    results = vector_store.query(query)  # global fallback
```

This avoids managing a separate ChromaDB collection per tenant while still isolating content.

### Ticket Scoping
Every `Ticket` row has a `tenant_id` foreign key. The `/api/tickets` endpoint filters by the authenticated user's `tenant_id`:

- **Agent** — sees only tickets where `tenant_id` matches their assigned store
- **Store Admin** — same scope
- **Super Admin** — no filter; sees all tickets

### API Key Rotation
Super admins can rotate any store's API key from the Super Admin Panel. The old key is invalidated immediately — any widget still using it will get a `401` until it receives the new key.

## Seeded Tenants

| Tenant | `tenant_id` | Store Admin |
|---|---|---|
| ShopBD | `shopbd` | admin@shopbd.com |
| FashionBD | `fashionbd` | admin@fashionbd.com |
