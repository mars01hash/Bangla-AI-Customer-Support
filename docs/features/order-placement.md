# Order Placement Flow

Customers can place orders entirely through the chat — no separate form or checkout page needed.

## How It Works

The bot detects buy intent and enters a **multi-turn collection flow**:

```
Customer: "iPhone 15 কিনতে চাই"
    ↓ detected: order_placement
Bot: "দারুণ! অর্ডার করতে কিছু তথ্য দরকার। আপনার পুরো নাম বলুন?"

Customer: "Rahim Ahmed"
    ↓ detected: order_placement (mid-collection)
Bot: "ধন্যবাদ Rahim Ahmed! আপনার মোবাইল নম্বর দিন।"

Customer: "01712345678"
    ↓ detected: order_placement (mid-collection)
Bot: "চমৎকার! আপনার ডেলিভারি ঠিকানা বলুন।"

Customer: "House 12, Road 5, Dhanmondi, Dhaka"
    ↓ all fields collected → creates Order + Ticket
Bot: "আপনার অর্ডার সফলভাবে নেওয়া হয়েছে!
      অর্ডার আইডি: ORD-XK9P2A
      পণ্য: iPhone 15
      ..."
```

## Intent Detection

Buy intent is recognised across three scripts:

| Script | Examples |
|---|---|
| English | `"i want to buy"`, `"order now"`, `"place order"`, `"purchase this"` |
| Bangla | `"কিনতে চাই"`, `"অর্ডার করতে চাই"`, `"নিতে চাই"`, `"কিনব"` |
| Banglish | `"order korbo"`, `"kinbo"`, `"order debo"` |

The detector also catches affirmative responses to a bot offer (`"অর্ডার করতে চান?"` → customer says `"হ্যাঁ"`, `"korbo"`, `"yes"`, `"ok"`, etc.).

## State Tracking (Stateless)

The `order_placement` node does not use server-side session storage. It reconstructs collected fields by replaying message history on each turn:

```python
# Walk messages in order; whenever bot asks for X, next human reply = X value
for m in messages:
    if isinstance(m, AIMessage) and "আপনার নাম" in m.content:
        pending_field = "name"
    elif isinstance(m, HumanMessage) and pending_field:
        collected[pending_field] = m.content
        pending_field = None
```

This means the node is safe to restart or redeploy mid-conversation.

## What Gets Created

On completion, two database rows are created atomically:

| Model | What's stored |
|---|---|
| `Order` | `order_id`, `customer_name`, `items`, `status="pending"` |
| `Ticket` | `ticket_id`, product + mobile + address in description, `category="order"`, `status="open"` |

The support team sees the ticket in their [Agent Dashboard](../user-guide/agent-dashboard.md) and contacts the customer to confirm delivery details.
