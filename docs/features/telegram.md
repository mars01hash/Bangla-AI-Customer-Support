# Telegram Bot

The same AI agent graph that powers the web widget is also available as a Telegram bot.

## Setup

### Step 1 — Create a Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the prompts
3. Copy the token (format: `123456789:ABC-DefGhi...`)
4. Add it to `backend/.env`:

```env
TELEGRAM_BOT_TOKEN=123456789:ABC-DefGhi...
```

### Step 2 — Choose a Mode

=== "Polling (localhost)"
    No public URL needed. Best for local development.

    ```bash
    cd backend
    venv\Scripts\activate    # Windows
    python telegram_poll.py
    ```

=== "Webhook (production)"
    Requires a public HTTPS URL (your VPS, Railway, Render, etc. — or ngrok for testing).

    ```bash
    curl -X POST https://yourdomain.com/api/telegram/set-webhook \
      -H "Authorization: Bearer <super_admin_jwt>" \
      -d "webhook_url=https://yourdomain.com/api/telegram/webhook"
    ```

!!! warning
    Do **not** run polling and webhook simultaneously with the same bot token. Telegram will only deliver messages to one of them.

## How It Works

Incoming Telegram messages are routed through the same `support_graph` as web chat messages. Language detection, sentiment analysis, and all agent nodes behave identically. The bot replies in the detected language.

Session history is maintained per Telegram `chat_id` for the duration of the polling/webhook process lifetime.
