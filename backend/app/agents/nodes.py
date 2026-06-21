import re
import uuid
import json
import random
import logging
import datetime
import httpx
from typing import Dict, Any, List
from langchain_core.messages import AIMessage, HumanMessage

from app.config import settings
from app.agents.state import AgentState
from app.rag.vectorstore import vector_store
from app.database import SessionLocal
from app.models import Ticket, User, Order, Product

logger = logging.getLogger(__name__)

# --- Helper functions ---

def _has_pending_clarification(messages: list) -> bool:
    """Return True if the last AI message was asking the user a clarifying question."""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            text = msg.content.strip()
            lower = text.lower()
            return (
                text.endswith('?') or
                'could you' in lower or
                'can you' in lower or
                'please tell' in lower or
                'please provide' in lower or
                'please share' in lower or
                'please describe' in lower or
                'what is the' in lower or
                # Bangla question indicators
                text.endswith('য়') or   # ends with Bangla '?'
                ('বলুন' in text) or  # "বলুন"
                ('কি' in text and '?' in text)   # "কি" + ?
            )
    return False


def _is_mid_order_collection(messages: list) -> bool:
    """True if the last bot message was asking for name/mobile/address as part of order collection."""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            text = msg.content.lower()
            return any(k in text for k in [
                "full name", "your name", "আপনার নাম", "পুরো নাম",
                "mobile number", "phone number", "মোবাইল নম্বর", "ফোন নম্বর",
                "delivery address", "shipping address", "ঠিকানা", "ডেলিভারি ঠিকানা",
            ])
        break
    return False


def _bot_just_offered_order(messages: list) -> bool:
    """True if the last bot message ended with an offer to place an order."""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            text = msg.content.lower()
            return any(k in text for k in [
                "place the order", "place an order", "shall i help you place",
                "help you order", "would you like to order",
                "অর্ডার করতে চান", "অর্ডার দিতে চান", "কিনতে চান",
            ])
        break
    return False


def _is_affirmative(text: str) -> bool:
    t = text.lower().strip()
    return any(k in t for k in [
        "yes", "yeah", "yep", "ok", "okay", "sure", "go ahead", "proceed",
        "please", "i want", "i'll", "let's go", "do it",
        "হ্যাঁ", "জি", "ঠিক আছে", "করুন", "দিন", "নিতে চাই", "কিনতে চাই",
        "korbo", "kinbo", "nebo", "debo",  # Banglish affirmatives
    ])


def _has_buy_intent(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in [
        "i want to buy", "i want to order", "i'd like to buy", "i'll buy",
        "buy now", "place order", "order now", "add to cart", "purchase this",
        "কিনতে চাই", "অর্ডার করতে চাই", "অর্ডার দিতে চাই", "নিতে চাই",
        "কিনব", "অর্ডার করব", "এটা চাই",
        "order korbo", "kinbo", "order debo",  # Banglish buy intent
    ])


def _is_continuing_escalation(messages: list) -> bool:
    """Return True when mid-escalation: last bot msg was a clarifying question
    AND at least one prior human message explicitly requested escalation.
    """
    if not _has_pending_clarification(messages):
        return False
    for msg in messages:
        if isinstance(msg, HumanMessage) and classify_intent_heuristics(msg.content) == "escalation":
            return True
    return False


def _build_conversation_summary(messages: list) -> str:
    """Build a short summary of recent conversation turns for ticket context."""
    lines = []
    for msg in messages[-6:]:  # last 3 turns
        if isinstance(msg, HumanMessage):
            lines.append(f"Customer: {msg.content}")
        elif isinstance(msg, AIMessage):
            lines.append(f"Agent: {msg.content}")
    return "\n".join(lines)


def detect_language_heuristics(text: str) -> str:
    """Detect language by checking for Bangla Unicode blocks and English text."""
    bangla_pattern = re.compile(r'[ঀ-৿]')
    has_bangla = bool(bangla_pattern.search(text))
    english_words = re.findall(r'[a-zA-Z]+', text)
    has_english = len(english_words) > 0

    if has_bangla and has_english:
        return "mixed"
    elif has_bangla:
        return "bn"
    else:
        return "en"


def detect_sentiment_heuristics(text: str) -> str:
    """Analyze text for sentiment indicators in Bangla and English."""
    text_lower = text.lower()

    negatives = [
        "খারাপ", "বাজে", "পচা",
        "ভুল", "সমস্যা", "দেরি",
        "ঘৃণা", "কাজ করছে না",
        "অযোগ্য", "হতাশ",
        "ফালতু", "নষ্ট", "ক্ষতি",
        "অভিযোগ",
        "bad", "worst", "broken", "angry", "hate", "error", "fail", "slow",
        "delay", "useless", "disappointed", "not working", "terrible",
        "annoyed", "frustrated", "refund",
    ]

    positives = [
        "ভালো", "সুন্দর",
        "ধন্যবাদ", "সেরা",
        "দুর্দান্ত",
        "অসাধারণ",
        "good", "great", "nice", "awesome", "perfect", "thanks",
        "thank you", "helpful", "love", "excellent", "happy", "satisfied",
    ]

    for word in negatives:
        if word in text_lower:
            return "negative"
    for word in positives:
        if word in text_lower:
            return "positive"
    return "neutral"


def classify_intent_heuristics(text: str) -> str:
    """Route requests by matching trigger keywords for categories."""
    text_lower = text.lower()

    # A bare order ID (ORD-XXXXX or #12345) should always route to order
    if re.match(r'^\s*(ord-[\w]+|#\d+)\s*$', text_lower):
        return "order"

    escalate_words = [
        "হিউম্যান", "মানুষ", "এজেন্ট", "কর্মকর্তা", "সরাসরি",
        "human", "agent", "escalate", "talk to", "representative", "manager", "speak to person",
    ]
    product_words = [
        # Purchase / price intent
        "দাম", "মূল্য", "কিনতে", "কিনব", "কিনতে চাই", "কিনতে পারি",
        # Features / specs
        "ফিচার", "বৈশিষ্ট্য", "স্পেক", "স্পেসিফিকেশন", "রিভিউ", "বিস্তারিত",
        # Comparison
        "তুলনা", "তুলনামূলক", "কোনটা ভালো", "কোনটা কিনব", "পার্থক্য", "কোনটা নেব",
        # Recommendation
        "সেরা", "সাজেস্ট", "রেকমেন্ড", "পরামর্শ", "উপযুক্ত", "ভালো হবে",
        # Budget / search
        "বাজেট", "সস্তা", "কম দামে", "এর মধ্যে", "হাজার টাকায়",
        # Catalog browsing
        "কী কী আছে", "কি আছে", "দেখান", "লিস্ট",
        # English — purchase / info
        "buy", "purchase", "price of", "how much", "feature", "spec",
        "review", "tell me about", "detail", "description", "available",
        # English — compare / recommend
        "compare", " vs ", "versus", "difference", "recommend", "suggest",
        "best", "which one", "worth it", "should i buy", "good for",
        # English — budget / search
        "budget", "affordable", "cheap", "under", "within", "show me", "what do you have",
    ]
    billing_words = [
        "বিল", "কার্ড", "পেমেন্ট", "খরচ", "রিসিট", "ইনভয়স", "রিফান্ড", "ফেরত",
        "billing", "payment", "charge", "invoice", "receipt", "refund",
    ]
    order_words = [
        "অর্ডার", "ডেলিভারি", "শিপিং", "কোথায়", "ট্র্যাক",
        "order", "delivery", "shipping", "track", "package", "where is",
    ]
    complaint_words = [
        "অভিযোগ", "নালিশ", "বাজে", "খারাপ", "ফালতু", "ঠকিয়েছে",
        "complaint", "issue", "problem", "disappointed", "scam", "damaged", "broken",
    ]
    greeting_words = [
        "হ্যালো", "হাই", "সালাম", "আদাব",
        "hello", "hi", "hey", "assalamualaikum",
    ]

    for word in escalate_words:
        if word in text_lower:
            return "escalation"
    for word in product_words:
        if word in text_lower:
            return "product"
    for word in complaint_words:
        if word in text_lower:
            return "complaint"
    for word in billing_words:
        if word in text_lower:
            return "billing"
    for word in order_words:
        if word in text_lower:
            return "order"
    for word in greeting_words:
        if word in text_lower:
            return "greeting"
    return "faq"


def query_llm_api(prompt: str, system_prompt: str = "") -> str:
    """Call external LLM based on settings, or fallback to heuristics."""
    if settings.LLM_PROVIDER == "mock":
        return ""

    try:
        if settings.LLM_PROVIDER == "openai":
            headers = {"Authorization": f"Bearer {settings.LLM_API_KEY}"}
            payload = {
                "model": settings.LLM_MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            }
            res = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload, headers=headers, timeout=15,
            )
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
            logger.error(f"OpenAI API returned {res.status_code}: {res.text[:200]}")

        elif settings.LLM_PROVIDER == "groq":
            headers = {"Authorization": f"Bearer {settings.LLM_API_KEY}"}
            payload = {
                "model": settings.LLM_MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            }
            res = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload, headers=headers, timeout=15,
            )
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
            logger.error(f"Groq API returned {res.status_code}: {res.text[:200]}")

        elif settings.LLM_PROVIDER == "openrouter":
            headers = {
                "Authorization": f"Bearer {settings.LLM_API_KEY}",
                "HTTP-Referer": "https://github.com/nlp-customer-support-bangla",
            }
            payload = {
                "model": settings.LLM_MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            }
            for attempt in range(3):
                res = httpx.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    json=payload, headers=headers, timeout=60,
                )
                if res.status_code == 200:
                    return res.json()["choices"][0]["message"]["content"]
                if res.status_code == 429 and attempt < 2:
                    import time as _time
                    wait = 10 * (attempt + 1)
                    logger.warning(f"OpenRouter 429 rate-limit, retrying in {wait}s (attempt {attempt+1})")
                    _time.sleep(wait)
                    continue
                logger.error(f"OpenRouter API returned {res.status_code}: {res.text[:200]}")
                break

        elif settings.LLM_PROVIDER == "huggingface":
            headers = {"Authorization": f"Bearer {settings.LLM_API_KEY}"}
            res = httpx.post(
                f"https://api-inference.huggingface.co/models/{settings.LLM_MODEL_NAME}",
                json={"inputs": f"System: {system_prompt}\nUser: {prompt}\nAssistant:"},
                headers=headers,
                timeout=15,
            )
            if res.status_code == 200:
                result = res.json()
                if isinstance(result, list) and result:
                    return result[0].get("generated_text", "")
                return str(result)
            logger.error(f"HuggingFace API returned {res.status_code}: {res.text[:200]}")

    except Exception as e:
        logger.error(f"Error querying LLM ({settings.LLM_PROVIDER}): {e}")

    return ""


# --- Node Implementations ---

def language_sentiment_detector_node(state: AgentState) -> Dict[str, Any]:
    """Node: Analyzes language, sentiment, and classifies customer intent."""
    current_message = state["current_message"]

    preferred = state.get("preferred_language")
    lang = preferred if preferred in ("bn", "en") else detect_language_heuristics(current_message)
    sentiment = detect_sentiment_heuristics(current_message)

    # If mid-escalation clarification flow, keep routing to escalation
    messages = state.get("messages", [])
    if _is_continuing_escalation(messages):
        category = "escalation"
        logger.info("Node [Detector] - Escalation continuation detected, forcing category=escalation")
    elif _is_mid_order_collection(messages):
        category = "order_placement"
        logger.info("Node [Detector] - Mid order-collection flow detected, routing to order_placement")
    elif _has_buy_intent(current_message):
        category = "order_placement"
        logger.info("Node [Detector] - Explicit buy intent detected, routing to order_placement")
    elif _bot_just_offered_order(messages) and _is_affirmative(current_message):
        category = "order_placement"
        logger.info("Node [Detector] - Affirmative response to order offer, routing to order_placement")
    else:
        category = classify_intent_heuristics(current_message)

    logger.info(f"Node [Detector] - Lang: {lang}, Sentiment: {sentiment}, Category: {category}")

    return {
        "detected_language": lang,
        "detected_sentiment": sentiment,
        "category": category,
    }


def greeting_agent_node(state: AgentState) -> Dict[str, Any]:
    """Node: Handles standard greetings in Bangla or English."""
    lang = state["detected_language"]

    llm_resp = query_llm_api(
        prompt=state["current_message"],
        system_prompt=(
            f"You are ShopBD's friendly AI customer support agent. "
            f"Greet the customer briefly, then answer any question they've included in the same message. "
            f"ShopBD policies: 7-day returns (unused + original packaging), "
            f"delivery 2-3 days Dhaka / 4-5 days outside Dhaka, "
            f"payments: bKash, Nagad, Rocket, Visa/Mastercard, Cash on Delivery. "
            f"Language: {lang}. Keep it to 3-4 sentences."
        ),
    )

    if llm_resp:
        answer = llm_resp
    elif lang in ["bn", "mixed"]:
        answer = (
            "হ্যালো! আমাদের "
            "কাস্টমার সাপোর্ট "
            "পোর্টালে আপনাকে "
            "স্বাগতম। আপনাকে "
            "কীভাবে সাহায্য "
            "করতে পারি?"
        )
    else:
        answer = "Hello! Welcome to our customer support. How can I help you today?"

    return {
        "answer": answer,
        "confidence_score": 1.0,
        "sources": [],
        "messages": [AIMessage(content=answer)],
    }


def faq_agent_node(state: AgentState) -> Dict[str, Any]:
    import json as _json
    query = state["current_message"]
    lang = state["detected_language"]
    messages = state.get("messages", [])
    tenant_id = state.get("tenant_id")

    history_lines = []
    for m in messages[-8:]:
        if isinstance(m, HumanMessage):
            history_lines.append(f"Customer: {m.content}")
        elif isinstance(m, AIMessage):
            history_lines.append(f"Assistant: {m.content}")
    history_str = "\n".join(history_lines)

    try:
        meta = {"tenant_id": tenant_id} if tenant_id else None
        retrieved = vector_store.query_documents(query, n_results=4, metadata_filter=meta)
        if not retrieved and tenant_id:
            retrieved = vector_store.query_documents(query, n_results=4)
        kb_context = "\n\n".join(doc["content"] for doc in retrieved) if retrieved else ""
        confidence = float(sum(d["confidence_score"] for d in retrieved) / len(retrieved)) if retrieved else 0.0
        sources = [{"source": d["metadata"].get("source", "KB"), "snippet": d["content"][:150]} for d in retrieved]
    except Exception:
        kb_context, confidence, sources = "", 0.0, []

    try:
        db = SessionLocal()
        products = db.query(Product).filter(Product.in_stock == True).all()
        db.close()
        catalog = "\n".join(
            f"• {p.name}" + (f" ({p.name_bn})" if p.name_bn else "") + f" — ৳{int(p.price):,} [{p.category}]"
            for p in products
        )
    except Exception:
        catalog = ""

    system_prompt = (
        "You are ShopBD's AI customer support assistant - friendly, knowledgeable, and genuinely helpful.\n\n"
        "ShopBD is a Bangladeshi ecommerce platform. You can help with:\n"
        "- Product questions, comparisons, recommendations, pricing\n"
        "- Order tracking (ask for order ID if needed)\n"
        "- Store policies: delivery (2-3 days Dhaka, 4-5 days outside), 7-day returns, bKash/Nagad/card/COD\n"
        "- General shopping advice, gifting ideas, tech questions\n"
        "- Anything else the customer needs\n\n"
        + (f"Available products:\n{catalog}\n\n" if catalog else "")
        + (f"Knowledge base context:\n{kb_context}\n\n" if kb_context else "")
        + (f"Conversation history:\n{history_str}\n\n" if history_str else "")
        + "Be conversational, warm, and direct. Never say 'I don't understand'. "
        "If you genuinely can't help, offer to connect them with a human agent. "
        f"Language: {lang}. Keep responses concise and natural."
    )

    llm_resp = query_llm_api(prompt=query, system_prompt=system_prompt)

    if llm_resp:
        answer = llm_resp
    elif kb_context:
        answer = kb_context[:400]
    elif lang in ["bn", "mixed"]:
        answer = "আমি আপনাকে সাহায্য করতে চাই! একটু বিস্তারিত বলুন — অর্ডার, পণ্য, নাকি অন্য কিছু?"
    else:
        answer = "I'm here to help! Could you give me a bit more detail - is this about an order, a product, or something else?"

    return {
        "answer": answer,
        "confidence_score": max(confidence, 0.5),
        "sources": sources,
        "messages": [AIMessage(content=answer)],
    }


def order_support_agent_node(state: AgentState) -> Dict[str, Any]:
    """Node: Handles order status lookups. Asks for Order ID if not provided."""
    lang = state["detected_language"]
    msg = state["current_message"]
    messages = state.get("messages", [])

    order_match = re.search(r'(ord-[\w]+|#\d+|\d{5})', msg.lower())
    raw_id = order_match.group(1).upper() if order_match else None

    if raw_id:
        if raw_id.startswith('#'):
            db_order_id = 'ORD-' + raw_id[1:]
        elif re.match(r'^\d+$', raw_id):
            db_order_id = 'ORD-' + raw_id
        else:
            db_order_id = raw_id
    else:
        db_order_id = None

    # No order ID — also check recent messages in case user gave it earlier
    if not db_order_id:
        for prev_msg in reversed(messages):
            if isinstance(prev_msg, HumanMessage):
                m = re.search(r'(ord-[\w]+|#\d+|\d{5})', prev_msg.content.lower())
                if m:
                    raw = m.group(1).upper()
                    if raw.startswith('#'):
                        db_order_id = 'ORD-' + raw[1:]
                    elif re.match(r'^\d+$', raw):
                        db_order_id = 'ORD-' + raw
                    else:
                        db_order_id = raw
                    break

    order = None
    if db_order_id:
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.order_id == db_order_id).first()
        except Exception as e:
            logger.error(f"DB lookup failed for order {db_order_id}: {e}")
        finally:
            db.close()

    if order:
        status_map = {
            "processing":       ("প্রক্রিয়াধীন", "processing"),
            "shipped":          ("শিপ করা হয়েছে", "shipped"),
            "out_for_delivery": ("ডেলিভারিতে আছে", "out for delivery"),
            "delivered":        ("ডেলিভারি সম্পন্ন", "delivered"),
            "cancelled":        ("বাতিল", "cancelled"),
        }
        bn_status, en_status = status_map.get(order.status, (order.status, order.status))
        delivery_bn = f" আনুমানিক ডেলিভারি: {order.estimated_delivery}।" if order.estimated_delivery else ""
        delivery_en = f" Estimated delivery: {order.estimated_delivery}." if order.estimated_delivery else ""

        if lang in ["bn", "mixed"]:
            answer = (
                f"আপনার অর্ডার {order.order_id} পাওয়া গেছে।\n"
                f"গ্রাহক: {order.customer_name}\n"
                f"স্ট্যাটাস: {bn_status}{delivery_bn}"
            )
        else:
            answer = (
                f"Order {order.order_id} found.\n"
                f"Customer: {order.customer_name}\n"
                f"Status: {en_status}{delivery_en}"
            )
        confidence = 1.0

    elif db_order_id:
        llm_resp = query_llm_api(
            prompt=f"Order ID {db_order_id} was not found.",
            system_prompt=(
                f"Tell the customer their order ID '{db_order_id}' was not found. "
                f"Apologize and ask them to double-check the ID or provide it again. "
                f"Language: {lang}."
            ),
        )
        if llm_resp:
            answer = llm_resp
        elif lang in ["bn", "mixed"]:
            answer = f"দুঃখিত, {db_order_id} নম্বরের কোনো অর্ডার পাওয়া যায়নি। আইডিটি পুনরায় যাচাই করুন অথবা অন্য কোনো আইডি দিয়ে চেষ্টা করুন?"
        else:
            answer = f"Sorry, no order with ID '{db_order_id}' was found. Could you double-check the order ID and try again?"
        confidence = 0.5

    else:
        # No order ID at all — ask for it conversationally
        llm_resp = query_llm_api(
            prompt=msg,
            system_prompt=(
                f"The customer wants to check on their order but hasn't provided an order ID. "
                f"Politely ask for their Order ID (format: ORD-XXXXX or #XXXXX). "
                f"Language: {lang}. One sentence."
            ),
        )
        if llm_resp:
            answer = llm_resp
        elif lang in ["bn", "mixed"]:
            answer = "অর্ডার স্ট্যাটাস দেখতে আপনার অর্ডার আইডিটি জানান (যেমন: ORD-12345 বা #12345)?"
        else:
            answer = "Sure, I can check that for you! Could you please share your Order ID? (e.g., ORD-12345 or #12345)"
        confidence = 0.9

    return {
        "answer": answer,
        "confidence_score": confidence,
        "sources": [],
        "messages": [AIMessage(content=answer)],
    }


def billing_agent_node(state: AgentState) -> Dict[str, Any]:
    """Node: Handles billing and payment questions."""
    lang = state["detected_language"]

    llm_resp = query_llm_api(
        prompt=state["current_message"],
        system_prompt=(
            f"You are ShopBD's billing support assistant.\n\n"
            f"ShopBD accepted payment methods: bKash, Nagad, Rocket, Visa/Mastercard credit & debit cards, Cash on Delivery (COD).\n"
            f"Refund policy: 7-day returns, refunds processed in 3-5 working days back to original payment method.\n\n"
            f"If the customer asks about payment methods, pricing, or general billing info — answer directly and clearly.\n"
            f"If they report a specific issue (wrong charge, failed payment, refund request) — acknowledge it and ask one focused question to understand better.\n"
            f"Be helpful and concise. Language: {lang}."
        ),
    )

    if llm_resp:
        answer = llm_resp
    elif lang in ["bn", "mixed"]:
        answer = "বিলিং সমস্যায় আমি সাহায্য করতে পারি। আপনার সমস্যাটি কি — অতিরিক্ত চার্জ, পেমেন্ট ব্যর্থ, নাকি রিফান্ডের অনুরোধ?"
    else:
        answer = "I can help with your billing concern. Could you tell me more — was there an incorrect charge, a failed payment, or would you like to request a refund?"

    return {
        "answer": answer,
        "confidence_score": 0.85,
        "sources": [],
        "messages": [AIMessage(content=answer)],
    }


def product_agent_node(state: AgentState) -> Dict[str, Any]:
    import json as _json
    msg = state["current_message"]
    lang = state["detected_language"]
    messages = state.get("messages", [])

    history_lines = []
    for m in messages[-6:]:
        if isinstance(m, HumanMessage):
            history_lines.append(f"Customer: {m.content}")
        elif isinstance(m, AIMessage):
            history_lines.append(f"Assistant: {m.content}")
    history_str = "\n".join(history_lines)

    all_products = []
    db = SessionLocal()
    try:
        all_products = db.query(Product).filter(Product.in_stock == True).all()
    except Exception as e:
        logger.error(f"Product DB load failed: {e}")
    finally:
        db.close()

    def product_card(p):
        try:
            feats = _json.loads(p.features or "[]")
        except Exception:
            feats = []
        disc = ""
        if p.original_price and p.original_price > p.price:
            pct = int((1 - p.price / p.original_price) * 100)
            disc = f" ({pct}% OFF)"
        lines = [
            f"Product: {p.name}" + (f" / {p.name_bn}" if p.name_bn else ""),
            f"Price: ৳{int(p.price):,}{disc}" + (f" (was ৳{int(p.original_price):,})" if p.original_price else ""),
            f"Category: {p.category or 'general'}",
        ]
        if feats:
            lines.append(f"Features: {', '.join(feats)}")
        if p.description:
            lines.append(f"Description: {p.description}")
        return "\n".join(lines)

    def find_products(text):
        text_l = text.lower()
        found = []
        for p in all_products:
            if p.name.lower() in text_l or (p.name_bn and p.name_bn in text):
                found.append(p)
                continue
            words = [w for w in text_l.split() if len(w) > 3]
            if any(w in p.name.lower() for w in words):
                found.append(p)
        seen, unique = set(), []
        for p in found:
            if p.id not in seen:
                seen.add(p.id)
                unique.append(p)
        return unique

    msg_lower = msg.lower()

    # ── 1. COMPARISON ────────────────────────────────────────────────────────
    is_compare = any(k in msg_lower for k in ["compare", " vs ", "versus", "difference", "তুলনা", "পার্থক্য", "কোনটা ভালো", "কোনটা নেব"])
    if is_compare:
        matched = find_products(msg)
        if len(matched) >= 2:
            catalog = "\n\n".join(product_card(p) for p in matched[:3])
        elif len(matched) == 1:
            catalog = product_card(matched[0])
            alts = [p for p in all_products if p.category == matched[0].category and p.id != matched[0].id][:2]
            if alts:
                catalog += "\n\nSimilar alternatives:\n" + "\n\n".join(product_card(p) for p in alts)
        else:
            catalog = "\n\n".join(product_card(p) for p in all_products[:6])
        system_prompt = (
            "You are ShopBD's expert product advisor. The customer wants to compare products.\n\n"
            f"Available product data:\n{catalog}\n\n"
            + (f"Conversation context:\n{history_str}\n\n" if history_str else "")
            + f"Give a clear, friendly comparison: key differences, who each is best for, and a final recommendation. "
            f"Use bullets or a table. Language: {lang}. Under 200 words."
        )
        llm_resp = query_llm_api(prompt=msg, system_prompt=system_prompt)
        answer = llm_resp or ("এই পণ্যগুলো তুলনা করছি।" if lang in ("bn", "mixed") else "Let me compare these for you.")
        return {"answer": answer, "confidence_score": 0.9, "sources": [], "messages": [AIMessage(content=answer)]}

    # ── 2. BUDGET / PRICE RANGE SEARCH ───────────────────────────────────────
    budget_match = re.search(r'(\d[\d,]+)', msg.replace(',', ''))
    has_budget_context = any(k in msg_lower for k in ["under", "within", "budget", "এর মধ্যে", "হাজার", "সস্তা", "কম দামে", "affordable", "cheap"])
    if budget_match and has_budget_context:
        budget = int(budget_match.group(1))
        if budget > 500:
            matched = [p for p in all_products if p.price <= budget]
            if matched:
                catalog = "\n\n".join(product_card(p) for p in matched[:5])
                system_prompt = (
                    "You are ShopBD's helpful shopping assistant.\n\n"
                    f"The customer has a budget of ৳{budget:,}. In-budget products:\n{catalog}\n\n"
                    + (f"Context:\n{history_str}\n\n" if history_str else "")
                    + f"Recommend the best 2-3 options: name, price, and why it's a good pick. "
                    f"Language: {lang}. Under 150 words."
                )
                llm_resp = query_llm_api(prompt=msg, system_prompt=system_prompt)
                answer = llm_resp or (f"৳{budget:,} বাজেটে এই পণ্যগুলো পাবেন।" if lang in ("bn", "mixed") else f"Best picks within ৳{budget:,}:")
                return {"answer": answer, "confidence_score": 0.9, "sources": [], "messages": [AIMessage(content=answer)]}

    # ── 3. RECOMMENDATION ────────────────────────────────────────────────────
    is_recommend = any(k in msg_lower for k in ["best", "recommend", "suggest", "which one", "সেরা", "কোনটা", "পরামর্শ", "ভালো হবে", "should i buy"])
    if is_recommend and all_products:
        cat_map = {
            "phone": "smartphone", "mobile": "smartphone", "ফোন": "smartphone",
            "laptop": "laptop", "ল্যাপটপ": "laptop", "computer": "laptop",
            "headphone": "audio", "earphone": "audio", "speaker": "audio", "হেডফোন": "audio",
        }
        filtered = all_products
        for kw, cat in cat_map.items():
            if re.search(r'\b' + re.escape(kw) + r'\b', msg_lower):
                filtered = [p for p in all_products if p.category == cat] or all_products
                break
        catalog = "\n\n".join(product_card(p) for p in filtered[:6])
        system_prompt = (
            "You are ShopBD's trusted product advisor for Bangladeshi shoppers.\n\n"
            f"Products available:\n{catalog}\n\n"
            + (f"Context:\n{history_str}\n\n" if history_str else "")
            + f"The customer wants a recommendation. Be decisive - name 1-2 best picks with clear reasons. "
            f"Mention price and key differentiator. End with a soft CTA. Language: {lang}. Under 120 words."
        )
        llm_resp = query_llm_api(prompt=msg, system_prompt=system_prompt)
        answer = llm_resp or ("সেরা বিকল্প সাজেস্ট করছি।" if lang in ("bn", "mixed") else "Here's my recommendation:")
        return {"answer": answer, "confidence_score": 0.9, "sources": [], "messages": [AIMessage(content=answer)]}

    # ── 4. CATALOG BROWSE ────────────────────────────────────────────────────
    is_browse = any(k in msg_lower for k in ["what do you have", "show me", "list", "কী আছে", "কি আছে", "দেখান", "লিস্ট"])
    if is_browse and all_products:
        cat_map = {"phone": "smartphone", "mobile": "smartphone", "laptop": "laptop", "headphone": "audio", "speaker": "audio", "ফোন": "smartphone", "ল্যাপটপ": "laptop"}
        filtered = all_products
        for kw, cat in cat_map.items():
            if re.search(r'\b' + re.escape(kw) + r'\b', msg_lower):
                filtered = [p for p in all_products if p.category == cat] or all_products
                break
        catalog = "\n".join(
            f"• {p.name}" + (f" ({p.name_bn})" if p.name_bn else "") + f" — ৳{int(p.price):,}"
            for p in filtered
        )
        system_prompt = (
            f"You are ShopBD's shopping assistant. Present these products:\n{catalog}\n\n"
            f"List them clearly, then ask what category or budget they have in mind. Language: {lang}. Keep it short."
        )
        llm_resp = query_llm_api(prompt=msg, system_prompt=system_prompt)
        answer = llm_resp or catalog
        return {"answer": answer, "confidence_score": 0.9, "sources": [], "messages": [AIMessage(content=answer)]}

    # ── 5. SPECIFIC PRODUCT QUERY ─────────────────────────────────────────────
    matched = find_products(msg)
    product = matched[0] if matched else None

    if product:
        try:
            features = _json.loads(product.features or "[]")
        except Exception:
            features = []
        pct_str = ""
        if product.original_price and product.original_price > product.price:
            pct = int((1 - product.price / product.original_price) * 100)
            pct_str = f" ({pct}% ছাড়)" if lang in ("bn", "mixed") else f" ({pct}% OFF)"
        price_str = f"৳{int(product.price):,}{pct_str}"
        system_prompt = (
            "You are ShopBD's enthusiastic sales assistant.\n\n"
            f"{product_card(product)}\n\n"
            + (f"Conversation context:\n{history_str}\n\n" if history_str else "")
            + f"Customer message: {msg}\n\n"
            "Answer the customer's question naturally. Cover price, features, discount. "
            f"End with a friendly CTA. Language: {lang}. Under 120 words."
        )
        llm_resp = query_llm_api(prompt=msg, system_prompt=system_prompt)
        if llm_resp:
            answer = llm_resp
        elif lang in ("bn", "mixed"):
            answer = f"**{product.name}** পাওয়া যাচ্ছে মাত্র {price_str}!\n\n" + "\n".join(f"✓ {f}" for f in features[:3]) + "\n\nঅর্ডার করতে চান?"
        else:
            answer = f"**{product.name}** is available for {price_str}!\n\n" + "\n".join(f"✓ {f}" for f in features[:3]) + "\n\nShall I help you place the order?"
    else:
        catalog_summary = "\n".join(f"• {p.name} — ৳{int(p.price):,} [{p.category}]" for p in all_products)
        try:
            rag = vector_store.query_documents(msg, n_results=2)
            kb = "\n".join(r["document"] for r in rag) if rag else ""
        except Exception:
            kb = ""
        system_prompt = (
            "You are ShopBD's helpful shopping assistant.\n\n"
            f"Catalog:\n{catalog_summary}\n\n"
            + (f"KB: {kb}\n\n" if kb else "")
            + (f"Context:\n{history_str}\n\n" if history_str else "")
            + f"Customer asked: {msg}\n"
            "Help them. If not in catalog, suggest closest alternatives. "
            f"Language: {lang}. Under 120 words."
        )
        llm_resp = query_llm_api(prompt=msg, system_prompt=system_prompt)
        answer = llm_resp or ("দুঃখিত এই পণ্যটি আমাদের কাছে নেই।" if lang in ("bn", "mixed") else "That product isn't in our catalog right now. Can I suggest an alternative?")

    return {
        "answer": answer,
        "confidence_score": 0.9 if product else 0.6,
        "sources": [],
        "messages": [AIMessage(content=answer)],
    }


def order_placement_agent_node(state: AgentState) -> Dict[str, Any]:
    """Multi-turn node: collects name/mobile/address then creates order + staff ticket."""
    messages = state.get("messages", [])
    lang = state.get("detected_language", "en")
    current_msg = state["current_message"]

    # ── 1. Find which product the customer wants ──────────────────────────────
    product_name = None
    # Check current message first
    db = SessionLocal()
    all_prods = []
    try:
        all_prods = db.query(Product).all()
    except Exception:
        pass
    finally:
        db.close()

    def find_product_in_text(text):
        t = text.lower()
        for p in all_prods:
            if p.name.lower() in t or (p.name_bn and p.name_bn in text):
                return p.name
            words = [w for w in t.split() if len(w) > 3]
            if any(w in p.name.lower() for w in words):
                return p.name
        return None

    product_name = find_product_in_text(current_msg)
    if not product_name:
        for m in reversed(messages):
            if isinstance(m, (HumanMessage, AIMessage)):
                product_name = find_product_in_text(m.content)
                if product_name:
                    break

    # ── 2. Determine what has already been collected from history ─────────────
    collected = {"name": None, "mobile": None, "address": None}

    # Walk messages in order; each time bot asks for X, the next human reply = X value
    pending_field = None
    for m in messages:
        if isinstance(m, AIMessage):
            text = m.content.lower()
            if any(k in text for k in ["full name", "your name", "আপনার নাম", "পুরো নাম"]):
                pending_field = "name"
            elif any(k in text for k in ["mobile number", "phone number", "মোবাইল নম্বর", "ফোন নম্বর"]):
                pending_field = "mobile"
            elif any(k in text for k in ["delivery address", "shipping address", "ঠিকানা", "ডেলিভারি ঠিকানা"]):
                pending_field = "address"
        elif isinstance(m, HumanMessage) and pending_field:
            collected[pending_field] = m.content.strip()
            pending_field = None

    # Current message fills whichever field was pending
    if pending_field and current_msg.strip():
        collected[pending_field] = current_msg.strip()

    # ── 3. Ask for next missing field or create order ─────────────────────────
    if not collected["name"]:
        if lang in ("bn", "mixed"):
            answer = "দারুণ! অর্ডার করতে কিছু তথ্য দরকার। প্রথমে আপনার **পুরো নাম** বলুন?"
        else:
            p = f" ({product_name})" if product_name else ""
            answer = f"Great{p}! To place your order I need a few details. First, what's your **full name**?"

    elif not collected["mobile"]:
        name = collected["name"]
        if lang in ("bn", "mixed"):
            answer = f"ধন্যবাদ {name}! আপনার **মোবাইল নম্বর** দিন (যেমন: 01XXXXXXXXX)।"
        else:
            answer = f"Thanks, {name}! What's your **mobile number**? (e.g., 01XXXXXXXXX)"

    elif not collected["address"]:
        if lang in ("bn", "mixed"):
            answer = "চমৎকার! এখন আপনার **ডেলিভারি ঠিকানা** বলুন (বাড়ি নম্বর, রাস্তা, এলাকা, জেলা)।"
        else:
            answer = "Almost done! What's your **delivery address**? (house/road/area/district)"

    else:
        # All collected — create order + ticket
        name    = collected["name"]
        mobile  = collected["mobile"]
        address = collected["address"]
        prod    = product_name or "Unknown product"
        order_id = "ORD-" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=6))
        ticket_id = "TKT-" + "".join(random.choices("0123456789", k=6))

        db2 = SessionLocal()
        try:
            new_order = Order(
                order_id=order_id,
                customer_name=name,
                customer_email="pending@shopbd.com",
                status="pending",
                items=json.dumps([prod]),
                total_amount=0.0,
            )
            db2.add(new_order)

            new_ticket = Ticket(
                ticket_id=ticket_id,
                customer_name=name,
                email="pending@shopbd.com",
                category="order",
                priority="normal",
                status="open",
                description=(
                    f"New order placed via chat bot.\n"
                    f"Product: {prod}\n"
                    f"Mobile: {mobile}\n"
                    f"Delivery address: {address}\n"
                    f"Order ID: {order_id}"
                ),
                sentiment="positive",
            )
            db2.add(new_ticket)
            db2.commit()
            success = True
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            success = False
            db2.rollback()
        finally:
            db2.close()

        if success:
            if lang in ("bn", "mixed"):
                answer = (
                    f"আপনার অর্ডার সফলভাবে নেওয়া হয়েছে!\n\n"
                    f"অর্ডার আইডি: {order_id}\n"
                    f"পণ্য: {prod}\n"
                    f"নাম: {name}\n"
                    f"মোবাইল: {mobile}\n"
                    f"ঠিকানা: {address}\n\n"
                    f"আমাদের সাপোর্ট টিম শীঘ্রই আপনার সাথে যোগাযোগ করবে। ধন্যবাদ!"
                )
            else:
                answer = (
                    f"Your order has been placed successfully!\n\n"
                    f"Order ID: {order_id}\n"
                    f"Product: {prod}\n"
                    f"Name: {name}\n"
                    f"Mobile: {mobile}\n"
                    f"Address: {address}\n\n"
                    f"Our support team will contact you shortly to confirm. Thank you!"
                )
        else:
            if lang in ("bn", "mixed"):
                answer = "দুঃখিত, অর্ডার প্রক্রিয়ায় সমস্যা হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।"
            else:
                answer = "Sorry, there was an error placing your order. Please try again or contact support."

    return {
        "answer": answer,
        "confidence_score": 0.95,
        "sources": [],
        "messages": [AIMessage(content=answer)],
    }


def complaint_agent_node(state: AgentState) -> Dict[str, Any]:
    """Node: Receives complaints. Asks what went wrong first, then escalates on follow-up."""
    lang = state["detected_language"]
    messages = state.get("messages", [])

    # If we've already asked a clarifying question, route to escalation now
    if _has_pending_clarification(messages):
        logger.info("Complaint: clarification collected — rerouting to escalation.")
        return {"category": "escalation"}

    # First visit: ask what went wrong before escalating
    logger.info("Complaint: asking clarifying question before escalating.")
    llm_resp = query_llm_api(
        prompt=state["current_message"],
        system_prompt=(
            f"The customer is filing a complaint. Empathize sincerely and ask one specific "
            f"question to understand what went wrong (e.g. order, product quality, delivery, "
            f"payment, or service). Do NOT create a ticket yet. "
            f"Keep it to 2 sentences ending with a question mark. Language: {lang}."
        ),
    )
    if llm_resp:
        answer = llm_resp
    elif lang in ["bn", "mixed"]:
        answer = (
            "আপনার অসুবিধার জন্য "
            "আমি সত্যিই দুঃখিত। "
            "ঠিক কী হয়েছে জানালে "
            "আমি আরো ভালোভাবে সাহায্য "
            "করতে পারব — এটা কি "
            "অর্ডার, পেমেন্ট, "
            "ডেলিভারি, নাকি অন্য "
            "কিছু নিয়ে?"
        )
    else:
        answer = (
            "I'm sorry to hear you're having trouble. "
            "Could you tell me what specifically went wrong — was it related to an order, "
            "delivery, payment, or something else?"
        )
    return {
        "answer": answer,
        "confidence_score": 1.0,
        "sources": [],
        "messages": [AIMessage(content=answer)],
    }


def escalation_agent_node(state: AgentState) -> Dict[str, Any]:
    """Node: Asks clarifying questions before creating a support ticket."""
    lang = state["detected_language"]
    query = state["current_message"]
    sentiment = state["detected_sentiment"]
    messages = state.get("messages", [])

    # If no clarifying question has been asked yet, ask first — don't create ticket
    if not _has_pending_clarification(messages):
        logger.info("Escalation: no prior clarification — asking question before ticket creation.")
        llm_resp = query_llm_api(
            prompt=query,
            system_prompt=(
                f"The customer needs support. Before creating a ticket, ask them 1-2 "
                f"specific questions to understand their issue: what exactly happened, "
                f"whether it involves an order (and if so, the order ID), and how urgent it is. "
                f"Be empathetic. Do NOT say you will create a ticket yet. "
                f"End with a question mark. Language: {lang}."
            ),
        )
        if llm_resp:
            answer = llm_resp
        elif lang in ["bn", "mixed"]:
            answer = (
                "আমি আপনাকে সাহায্য করতে "
                "চাই। একটু বিস্তারিত "
                "জানান — ঠিক কী সমস্যা "
                "হচ্ছে? যদি এটি অর্ডার "
                "সম্পর্কিত হয়, তাহলে "
                "অর্ডার আইডিটিও দিন?"
            )
        else:
            answer = (
                "I'd like to make sure we get this resolved for you. "
                "Could you describe what happened? If this is related to an order, "
                "please also share your Order ID so I can look into it right away."
            )

        return {
            "answer": answer,
            "confidence_score": 1.0,
            "ticket_escalated": False,
            "ticket_id": None,
            "sources": [],
            "messages": [AIMessage(content=answer)],
        }

    # Clarification was already given — now create the ticket
    logger.info("Escalation: clarification collected — creating support ticket.")
    conversation_summary = _build_conversation_summary(messages)
    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"

    db = SessionLocal()
    try:
        agent = db.query(User).filter(User.role == "agent").first()
        # Prefer tenant_id from state (widget flow); fall back to assigned agent's tenant
        ticket_tenant_id = state.get("tenant_id") or (agent.tenant_id if agent else None)
        ticket = Ticket(
            ticket_id=ticket_id,
            customer_name="Online Customer",
            email="customer@example.com",
            category=state.get("category", "general"),
            priority="high" if sentiment == "negative" else "medium",
            status="open",
            description=f"{query}\n\n--- Conversation context ---\n{conversation_summary}",
            sentiment=sentiment,
            assigned_agent_id=agent.id if agent else None,
            tenant_id=ticket_tenant_id,
        )
        db.add(ticket)
        db.commit()
        logger.info(f"Support ticket {ticket_id} created (tenant: {ticket_tenant_id}).")
    except Exception as e:
        logger.error(f"Error saving escalation ticket: {e}")
        db.rollback()
    finally:
        db.close()

    llm_resp = query_llm_api(
        prompt=f"Ticket {ticket_id} has been created for: {query}",
        system_prompt=(
            f"Inform the customer that a support ticket ({ticket_id}) has been created and a "
            f"human agent will follow up via email. Thank them for the details they provided. "
            f"Be warm and reassuring. Language: {lang}."
        ),
    )

    if llm_resp:
        answer = llm_resp
    elif lang in ["bn", "mixed"]:
        answer = (
            f"আপনার তথ্যের জন্য "
            f"ধন্যবাদ। আমি আপনার "
            f"জন্য একটি সাপোর্ট "
            f"টিকিট তৈরি করেছি "
            f"(টিকিট আইডি: {ticket_id})। "
            f"আমাদের একজন সাপোর্ট "
            f"এজেন্ট শীঘ্রই ইমেইলে "
            f"যোগাযোগ করবেন।"
        )
    else:
        answer = (
            f"Thank you for sharing those details. I've created a support ticket for you "
            f"(Ticket ID: {ticket_id}). One of our agents will follow up via email shortly "
            f"and make sure your issue is fully resolved."
        )

    return {
        "answer": answer,
        "confidence_score": 1.0,
        "ticket_escalated": True,
        "ticket_id": ticket_id,
        "sources": [],
        "messages": [AIMessage(content=answer)],
    }
