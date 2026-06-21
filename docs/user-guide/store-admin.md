# Store Admin Panel

**Route:** `/storeadmin`  
**Login (ShopBD):** `admin@shopbd.com` / `storepassword123`

The store admin manages everything for their store. The panel has six tabs.

## Overview Tab
- Live stats: open tickets, total conversations, KB entries, active agents
- Quick-start checklist: add KB entries → invite agents → copy embed code

## Knowledge Base Tab
Add Q&A pairs that the AI will use when answering customer questions. Each entry is embedded with LaBSE and stored in ChromaDB tagged with your `tenant_id`.

**Adding an entry:**
1. Enter a question and its answer
2. Click **Add Entry**
3. The entry is immediately searchable by the chatbot

**Deleting an entry:**
- Click the trash icon next to any entry
- The vector store document is removed on the next query cycle

!!! tip
    Write questions the way your customers actually phrase them. The vector search matches by semantic similarity, not exact keywords.

## Embed Code Tab
Copy the HTML snippet and paste it before the `</body>` tag on your website:

```html
<script>
  window.SHOPBOT_KEY   = "sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
  window.SHOPBOT_API   = "https://your-platform-domain.com";
  window.SHOPBOT_COLOR = "#6366f1";
</script>
<script src="https://your-platform-domain.com/api/widget.js" async></script>
```

`SHOPBOT_KEY` is your store's API key. Never share it publicly.

## Agents Tab
- **Invite agent** — enter an email address; the user is created (or linked) and assigned to your store
- **Remove agent** — unlinks the agent from your store; does not delete the user account

## Tickets Tab
View and manage customer support tickets scoped to your store:

| Column | Description |
|---|---|
| Ticket ID | Unique identifier (e.g. `TKT-ABC123`) |
| Customer | Name from ticket submission |
| Category | `order`, `billing`, `complaint`, `general` |
| Priority | `high` (negative sentiment) or `medium` |
| Status | `open`, `in_progress`, `resolved` |
| Assigned | Which agent is handling it |

Click any ticket to update its status or reassign it to a different agent.

## Settings Tab
- **Widget colour** — hex colour picker for the chat button and header
- **Welcome message** — the first message customers see when they open the widget
