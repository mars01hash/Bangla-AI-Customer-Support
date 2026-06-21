# ShopBD Storefront Demo

The platform ships with a full Bangladeshi ecommerce demo that shows the chatbot integrated into a real shopping flow.

**Route:** `/` (home page, accessible without login)

## Product Catalog

12 demo products across four categories:

| Category | Examples |
|---|---|
| Smartphones | iPhone 15, Samsung Galaxy S24 |
| Laptops | MacBook Pro M3, Dell XPS 15 |
| Audio | Sony WH-1000XM5, AirPods Pro |
| Fashion & Accessories | Various clothing and accessories |

All products have Bangla names (`name_bn`), prices in BDT (৳), and optional discounts.

## Shopping Flow

```
Browse  →  Add to Cart  →  Checkout  →  Payment  →  Order Confirmation
```

### Browse
- Grid layout with product cards showing name, Bangla name, price, discount badge
- Category filter tabs
- "Add to Cart" button on each card

### Cart
- Quantity controls (+ / −)
- Remove item
- Subtotal updates live

### Checkout
- Full name, phone number, delivery address
- Delivery method: **Standard** (2-3 days Dhaka, 4-5 outside) or **Express** (next day)

### Payment
Four methods supported:

| Method | UX |
|---|---|
| bKash | Enter phone number + OTP confirmation screen |
| Nagad | Enter phone number + OTP confirmation screen |
| Card | 16-digit number + expiry (MM/YY) + CVV |
| Cash on Delivery | No extra fields |

### Order Confirmation
- Displays generated Order ID (e.g. `ORD-XK9P2A`)
- **"Track in Chat"** button — pre-fills the chatbot with the order ID and auto-sends it, opening the order status lookup flow instantly

## Chat Integration

The chatbot floats over the storefront. Customers can:
- Ask about any product by name while browsing
- Express buy intent ("iPhone 15 kinbo") and complete the order via chat
- Ask about delivery, payment, or return policy at any point
- Track an order by clicking "Track in Chat" or typing the order ID
