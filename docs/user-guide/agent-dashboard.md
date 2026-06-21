# Agent Dashboard

**Route:** `/dashboard`  
**Login (ShopBD):** `agent@shopbd.com` / `agentpassword123`

Agents see a filtered view of their store's tickets plus analytics.

## Ticket Queue
- All open and in-progress tickets assigned to the agent's store
- Click a ticket to update status (`open` → `in_progress` → `resolved`)
- Tickets created by the chatbot include a conversation summary in the description

## Analytics
- Ticket volume over time
- Sentiment breakdown (positive / neutral / negative)
- Category distribution (order / billing / complaint / general)
- Resolution time averages

## Order Management
- View all orders placed via the chat or storefront
- Order IDs, customer names, items, status, and estimated delivery

## Knowledge Upload
Super admins can upload documents to the global knowledge base from the dashboard. Documents are chunked and indexed into ChromaDB and are available to all tenants as a fallback.
