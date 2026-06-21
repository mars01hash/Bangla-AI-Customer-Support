# Public Endpoints

No authentication required.

## Chat

### `POST /api/chat`
Main chat endpoint (session-based, no API key needed).

**Request:**
```json
{
  "message": "iPhone 15 এর দাম কত?",
  "session_id": "abc123",
  "preferred_language": "bn"
}
```

**Response:**
```json
{
  "answer": "iPhone 15 পাওয়া যাচ্ছে মাত্র ৳1,29,999!...",
  "session_id": "abc123",
  "category": "product",
  "confidence_score": 0.9,
  "sources": []
}
```

---

### `POST /api/widget/chat`
Widget chat. Requires `X-Api-Key` header to identify the tenant.

**Headers:**
```
X-Api-Key: sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Request / Response:** Same shape as `/api/chat`.

---

### `GET /api/widget/config`
Returns branding config for the widget.

**Query:** `?api_key=sk_...`

**Response:**
```json
{
  "store_name": "ShopBD",
  "welcome_message": "আমাদের কাস্টমার সাপোর্টে স্বাগতম!",
  "color": "#6366f1"
}
```

---

## Orders

### `POST /api/orders/place`
Place an ecommerce order from the storefront checkout.

**Request:**
```json
{
  "customer_name": "Rahim Ahmed",
  "customer_email": "rahim@example.com",
  "phone": "01712345678",
  "address": "House 12, Road 5, Dhanmondi, Dhaka",
  "items": [{"product_id": 1, "quantity": 1}],
  "payment_method": "bkash",
  "delivery_method": "standard"
}
```

**Response:**
```json
{
  "order_id": "ORD-XK9P2A",
  "status": "pending",
  "estimated_delivery": "2026-06-24"
}
```

---

### `GET /api/orders/track/{order_id}`
Track an order by ID.

**Response:**
```json
{
  "order_id": "ORD-XK9P2A",
  "customer_name": "Rahim Ahmed",
  "status": "shipped",
  "estimated_delivery": "2026-06-24"
}
```

---

## Feedback

### `POST /api/feedback`
Submit a thumbs up/down rating for a chat response.

**Request:**
```json
{
  "session_id": "abc123",
  "rating": 1
}
```

---

## Products

### `GET /api/products`
Returns all in-stock products.

**Response:**
```json
[
  {
    "id": 1,
    "name": "iPhone 15",
    "name_bn": "আইফোন ১৫",
    "price": 129999,
    "original_price": 139999,
    "category": "smartphone",
    "in_stock": true,
    "features": ["A16 Bionic chip", "48MP camera", "USB-C"]
  }
]
```
