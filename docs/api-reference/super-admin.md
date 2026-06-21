# Super Admin Endpoints

All endpoints require a JWT token with role `super_admin`.

**Auth header:**
```
Authorization: Bearer <jwt_token>
```

---

## Tenants

### `GET /api/tenants`
List all tenants (stores) on the platform.

**Response:**
```json
[
  {
    "id": "shopbd",
    "name": "ShopBD",
    "api_key": "sk_***...",
    "is_active": true,
    "created_at": "2026-01-15T10:00:00Z"
  }
]
```

### `POST /api/tenants`
Create a new tenant. API key is generated automatically.

**Request:**
```json
{
  "name": "ElectronicsBD",
  "admin_email": "admin@electronicsbd.com"
}
```

### `GET /api/tenants/{tenant_id}`
Get details for a specific tenant.

### `PUT /api/tenants/{tenant_id}`
Update tenant name or active status.

### `DELETE /api/tenants/{tenant_id}`
Delete a tenant and all associated data.

### `POST /api/tenants/{tenant_id}/rotate-key`
Generate a new API key for a tenant. The old key is invalidated immediately.

**Response:**
```json
{
  "api_key": "sk_yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy"
}
```

### `GET /api/tenants/{tenant_id}/stats`
Per-tenant analytics: tickets, conversations, KB entries, agent count.

---

## Users

### `GET /api/users`
List all users across all tenants.

**Response:**
```json
[
  {
    "id": 1,
    "email": "agent@shopbd.com",
    "role": "agent",
    "tenant_id": "shopbd"
  }
]
```

### `PUT /api/users/{user_id}`
Update a user's role or reassign them to a different tenant.

**Request:**
```json
{
  "role": "store_admin",
  "tenant_id": "fashionbd"
}
```
