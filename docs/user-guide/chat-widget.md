# Embedding the Chat Widget

## Embed Snippet

Paste this before the `</body>` tag on any website:

```html
<script>
  window.SHOPBOT_KEY   = "sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";  // your store's API key
  window.SHOPBOT_API   = "https://your-platform-domain.com";     // backend base URL
  window.SHOPBOT_COLOR = "#6366f1";                              // widget accent colour
</script>
<script src="https://your-platform-domain.com/api/widget.js" async></script>
```

Get your snippet from the [Embed Code tab](store-admin.md#embed-code-tab) in the Store Admin Panel.

## Widget Features

- **Floating button** — bottom-right corner, opens a chat drawer
- **Language toggle** — customers switch between Bangla and English; the agent graph respects this preference for every reply
- **Markdown rendering** — bot responses support bold, bullet lists, and code blocks
- **Auto-send prefill** — pass `?message=ORD-12345` in the URL to pre-fill and auto-send a message (used by the "Track in Chat" button on order confirmation pages)
- **Chat rating** — thumbs up/down feedback submitted to `/api/feedback`

## How Tenant Isolation Works

Every widget request includes your `SHOPBOT_KEY` as the `X-Api-Key` header:

```
POST /api/widget/chat
X-Api-Key: sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

The backend:
1. Looks up the tenant from the key
2. Queries ChromaDB filtered to that `tenant_id`
3. Falls back to global knowledge base if no match
4. Tags all created tickets with the `tenant_id`

Agents only see tickets belonging to their store.

## Widget Config Endpoint

The widget fetches branding on load:

```
GET /api/widget/config?api_key=sk_...
```

Returns:
```json
{
  "store_name": "ShopBD",
  "welcome_message": "আমাদের কাস্টমার সাপোর্টে স্বাগতম!",
  "color": "#6366f1"
}
```
