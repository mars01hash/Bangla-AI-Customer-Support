import re
import uuid
import logging
import datetime
import httpx
from typing import Dict, Any, List
from langchain_core.messages import AIMessage, HumanMessage

from app.config import settings
from app.agents.state import AgentState
from app.rag.vectorstore import vector_store
from app.database import SessionLocal
from app.models import Ticket, User, Order

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

    escalate_words = [
        "হিউম্যান", "মানুষ",
        "এজেন্ট", "কর্মকর্তা",
        "সরাসরি",
        "human", "agent", "escalate", "talk to", "representative", "manager", "speak to person",
    ]
    billing_words = [
        "বিল", "টাকা", "কার্ড",
        "পেমেন্ট", "খরচ",
        "রিসিট", "ইনভয়স",
        "billing", "payment", "money", "price", "charge", "invoice", "receipt",
    ]
    order_words = [
        "অর্ডার", "ডেলিভারি",
        "শিপিং", "পণ্য",
        "প্রোডাক্ট",
        "কোথায়", "ট্র্যাক",
        "order", "delivery", "shipping", "product", "track", "package", "where is",
    ]
    complaint_words = [
        "অভিযোগ", "নালিশ",
        "বাজে", "খারাপ",
        "ফালতু", "ঠকিয়েছে",
        "complaint", "issue", "claim", "problem", "disappointed", "sue", "scam",
    ]
    greeting_words = [
        "হ্যালো", "হাই",
        "কেমন", "সালাম",
        "আদাব",
        "hello", "hi", "hey", "greeting", "morning", "assalamualaikum", "adab",
    ]

    for word in escalate_words:
        if word in text_lower:
            return "escalation"
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

    lang = detect_language_heuristics(current_message)
    sentiment = detect_sentiment_heuristics(current_message)
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
            f"You are a friendly Bangla AI customer support agent. "
            f"Greet the customer warmly, introduce yourself briefly, and ask how you can help. "
            f"Respond in the user's language (detected: {lang}). Keep it to 2-3 sentences."
        ),
    )

    if llm_resp:
        answer = llm_resp
    elif lang in ["bn", "mixed"]:
        answer = (
            "হ্যালো! আমাদের "
            "কাস্টমার সাপোর্ট "
            "পোর্টালে আপনাকে "
            "স্বাগতম। আজ আপনাকে "
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
    """Node: RAG agent — queries vector store, asks for clarification when confidence is low."""
    query = state["current_message"]
    lang = state["detected_language"]
    messages = state.get("messages", [])

    tenant_id = state.get("tenant_id")
    metadata_filter = {"tenant_id": tenant_id} if tenant_id else None
    retrieved_docs = vector_store.query_documents(query, n_results=3, metadata_filter=metadata_filter)
    # Fall back to global KB if tenant KB has no results
    if not retrieved_docs and tenant_id:
        retrieved_docs = vector_store.query_documents(query, n_results=3)

    sources = []
    context_blocks = []
    for idx, doc in enumerate(retrieved_docs):
        src = doc["metadata"].get("source", f"Document-{idx + 1}")
        sources.append({
            "id": doc["id"],
            "source": src,
            "confidence": doc["confidence_score"],
            "snippet": doc["content"][:200] + "...",
        })
        context_blocks.append(f"Source: {src}\nContent: {doc['content']}")

    confidence = (
        float(sum(d["confidence_score"] for d in retrieved_docs) / len(retrieved_docs))
        if retrieved_docs else 0.0
    )

    # Low confidence — ask clarifying question instead of immediately escalating
    if confidence < 0.35:
        logger.info(f"RAG confidence {confidence:.2f} too low — asking clarifying question.")
        clarify_resp = query_llm_api(
            prompt=query,
            system_prompt=(
                f"You are a helpful customer support agent. The customer asked something you "
                f"couldn't find a clear answer for. Politely ask them to rephrase or give one "
                f"more specific detail (e.g. whether it's about an order, payment, or product). "
                f"Keep it to one friendly sentence ending with a question mark. "
                f"Respond in language: {lang}."
            ),
        )
        if clarify_resp:
            answer = clarify_resp
        elif lang in ["bn", "mixed"]:
            answer = (
                "দুঃখিত, আমি আপনার "
                "প্রশ্নটি পুরোপুরি "
                "বুঝতে পারিনি — "
                "এটা কি অর্ডার, "
                "পেমেন্ট, নাকি "
                "অন্য কিছু নিয়ে?"
            )
        else:
            answer = (
                "I want to make sure I give you the right answer — could you give me a bit more "
                "detail? For example, is this about an order, a payment, or something else?"
            )
        return {
            "answer": answer,
            "confidence_score": confidence,
            "sources": [],
            "messages": [AIMessage(content=answer)],
        }

    combined_context = "\n\n".join(context_blocks)
    llm_prompt = (
        f"Context:\n{combined_context}\n\n"
        f"Question: {query}\n\n"
        f"Answer using the context above. Be concise and helpful. "
        f"If the context doesn't fully cover the question, say so and offer to connect them with support. "
        f"Language: {lang}."
    )
    llm_resp = query_llm_api(
        prompt=llm_prompt,
        system_prompt="You are a helpful customer support knowledge assistant. Cite sources naturally.",
    )

    if llm_resp:
        answer = llm_resp
    else:
        sources_str = ", ".join(s["source"] for s in sources)
        if lang in ["bn", "mixed"]:
            answer = f"আমাদের নথি অনুসারে: {retrieved_docs[0]['content']}\n\n(উৎস: {sources_str})"
        else:
            answer = f"According to our knowledge base: {retrieved_docs[0]['content']}\n\n(Sources: {sources_str})"

    return {
        "answer": answer,
        "confidence_score": confidence,
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
            answer = f"দুঃখিত, {db_order_id} নম্বরের কোনো অর্ডার পাওয়া যায়নি। আইডিটি পুনরায় যাচাই করুন, নাকি অন্য কোনো আইডি দিয়ে চেষ্টা করুন?"
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
    """Node: Asks what the specific billing issue is before attempting to resolve."""
    lang = state["detected_language"]

    llm_resp = query_llm_api(
        prompt=state["current_message"],
        system_prompt=(
            f"You are a billing support agent. The customer has a billing or payment concern. "
            f"Ask one focused question to understand their specific issue "
            f"(e.g. wrong charge, payment failed, refund request, invoice error). "
            f"Be empathetic and end with a question mark. Language: {lang}."
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
        )
        db.add(ticket)
        db.commit()
        logger.info(f"Support ticket {ticket_id} created.")
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
