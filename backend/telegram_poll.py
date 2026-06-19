"""
Telegram polling bot for local development.
Use this when you don't have a public HTTPS URL for webhooks (e.g. running on localhost).

Usage:
    cd backend
    venv\\Scripts\\activate
    set TELEGRAM_BOT_TOKEN=your_token_here
    python telegram_poll.py

The bot will poll Telegram for new messages and forward them to the local FastAPI
chat endpoint at http://localhost:8090/api/chat, then reply to the user on Telegram.

Get your token from @BotFather on Telegram:
  1. Open Telegram and search for @BotFather
  2. Send /newbot and follow the prompts
  3. Copy the token and set TELEGRAM_BOT_TOKEN in your .env or shell
"""

import os
import sys
import time
import logging
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Load token from env or .env file
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
if not TOKEN:
    try:
        for line in open(os.path.join(os.path.dirname(__file__), "..", ".env")):
            line = line.strip()
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                TOKEN = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    except FileNotFoundError:
        pass

if not TOKEN:
    log.error("TELEGRAM_BOT_TOKEN not set. Add it to .env or set the environment variable.")
    sys.exit(1)

API_BASE = f"https://api.telegram.org/bot{TOKEN}"
CHAT_ENDPOINT = "http://localhost:8090/api/chat"


def get_updates(offset: int) -> list:
    try:
        r = httpx.get(f"{API_BASE}/getUpdates", params={"offset": offset, "timeout": 30}, timeout=35)
        if r.status_code == 200:
            return r.json().get("result", [])
    except Exception as e:
        log.warning(f"getUpdates error: {e}")
    return []


def send_message(chat_id: int, text: str) -> None:
    try:
        httpx.post(f"{API_BASE}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception as e:
        log.warning(f"sendMessage error: {e}")


def send_typing(chat_id: int) -> None:
    try:
        httpx.post(f"{API_BASE}/sendChatAction", json={"chat_id": chat_id, "action": "typing"}, timeout=5)
    except Exception:
        pass


def call_chat_api(text: str, session_id: str) -> str:
    try:
        r = httpx.post(
            CHAT_ENDPOINT,
            data={"message_in": text, "session_id": session_id},
            timeout=30
        )
        if r.status_code == 200:
            data = r.json()
            answer = data.get("answer", "")
            if data.get("ticket_escalated") and data.get("ticket_id"):
                answer += f"\n\n🎫 Ticket ID: {data['ticket_id']}"
            return answer
        log.error(f"Chat API returned {r.status_code}: {r.text[:200]}")
    except Exception as e:
        log.error(f"Chat API error: {e}")
    return "দুঃখিত, সার্ভারের সাথে যোগাযোগ করা যাচ্ছে না। (Sorry, could not reach the support server.)"


def handle_message(message: dict) -> None:
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if not text:
        send_message(chat_id, "শুধুমাত্র টেক্সট মেসেজ পাঠান। (Please send text messages only.)")
        return

    username = message["from"].get("username") or message["from"].get("first_name", "user")
    log.info(f"[{chat_id}] @{username}: {text}")

    if text == "/start":
        send_message(
            chat_id,
            "হ্যালো! আমি Bangla AI Customer Support Bot। বাংলা বা ইংরেজিতে আপনার প্রশ্ন লিখুন।\n\n"
            "Hello! I am Bangla AI Customer Support Bot. Ask me anything in Bangla or English."
        )
        return

    send_typing(chat_id)
    session_id = f"telegram-{chat_id}"
    answer = call_chat_api(text, session_id)
    send_message(chat_id, answer)
    log.info(f"[{chat_id}] Bot replied: {answer[:80]}...")


def main():
    log.info("Telegram polling bot starting...")
    log.info(f"Forwarding messages to: {CHAT_ENDPOINT}")

    # Confirm bot identity
    try:
        me = httpx.get(f"{API_BASE}/getMe", timeout=5).json()
        if me.get("ok"):
            bot = me["result"]
            log.info(f"Bot: @{bot['username']} ({bot['first_name']})")
        else:
            log.error(f"Invalid token or Telegram API error: {me}")
            sys.exit(1)
    except Exception as e:
        log.error(f"Could not connect to Telegram API: {e}")
        sys.exit(1)

    offset = 0
    log.info("Polling for messages... (Ctrl+C to stop)")

    while True:
        updates = get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1
            if "message" in update:
                handle_message(update["message"])
            elif "edited_message" in update:
                handle_message(update["edited_message"])
        if not updates:
            time.sleep(0.5)


if __name__ == "__main__":
    main()
