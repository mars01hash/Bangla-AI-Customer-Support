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
from app.models import Ticket, User

logger = logging.getLogger(__name__)

# --- Helper functions ---

def detect_language_heuristics(text: str) -> str:
    """Detect language by checking for Bangla Unicode blocks and English text."""
    bangla_pattern = re.compile(r'[\u0980-\u09ff]')
    has_bangla = bool(bangla_pattern.search(text))
    
    # Check if it has english words
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
        "খারাপ", "বাজে", "পচা", "ভুল", "সমস্যা", "দেরি", "ঘৃণা", "কাজ করছে না", "অযোগ্য", 
        "হতাশ", "ফালতু", "নষ্ট", "ক্ষতি", "অভিযোগ", "bad", "worst", "broken", "angry", 
        "hate", "error", "fail", "slow", "delay", "useless", "disappointed", "not working", 
        "terrible", "annoyed", "frustrated", "refund"
    ]
    
    positives = [
        "ভালো", "সুন্দর", "ধন্যবাদ", "সেরা", "দুর্দান্ত", "অসাধারণ", "ধন্যবাদ!", "উপকারী",
        "good", "great", "nice", "awesome", "perfect", "thanks", "thank you", "helpful", 
        "love", "excellent", "happy", "satisfied"
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
    
    escalate_words = ["হিউম্যান", "মানুষ", "এজেন্ট", "কর্মকর্তা", "সরাসরি", "human", "agent", "support", "escalate", "talk to", "representative", "manager"]
    billing_words = ["বিল", "টাকা", "কার্ড", "পেমেন্ট", "খরচ", "রিসিট", "ইনভয়েস", "billing", "payment", "money", "price", "charge", "invoice", "receipt"]
    order_words = ["অর্ডার", "ডেলিভারি", "শিপিং", "পণ্য", "প্রোডাক্ট", "কোথায়", "ট্র্যাক", "order", "delivery", "shipping", "product", "track", "package", "where is"]
    complaint_words = ["অভিযোগ", "নালিশ", "বাজে", "খারাপ", "ফালতু", "ঠকিয়েছে", "complaint", "issue", "claim", "problem", "disappointed", "sue", "scam"]
    greeting_words = ["হ্যালো", "হাই", "কেমন", "সালাম", "আদাব", "hello", "hi", "hey", "greeting", "morning", "assalamualaikum", "adab"]
    
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
        return "" # Calling module should handle mock return
        
    try:
        if settings.LLM_PROVIDER == "openai":
            headers = {"Authorization": f"Bearer {settings.LLM_API_KEY}"}
            payload = {
                "model": settings.LLM_MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            }
            res = httpx.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=10)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
                
        elif settings.LLM_PROVIDER == "groq":
            headers = {"Authorization": f"Bearer {settings.LLM_API_KEY}"}
            payload = {
                "model": settings.LLM_MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            }
            res = httpx.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=10)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
                
        elif settings.LLM_PROVIDER == "huggingface":
            # API endpoint for HF model inference
            headers = {"Authorization": f"Bearer {settings.LLM_API_KEY}"}
            res = httpx.post(
                f"https://api-inference.huggingface.co/models/{settings.LLM_MODEL_NAME}",
                json={"inputs": f"System: {system_prompt}\nUser: {prompt}\nAssistant:"},
                headers=headers,
                timeout=10
            )
            if res.status_code == 200:
                result = res.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "")
                return str(result)
                
    except Exception as e:
        logger.error(f"Error querying external LLM provider ({settings.LLM_PROVIDER}): {e}. Using mock/fallback.")
        
    return ""


# --- Node Implementations ---

def language_sentiment_detector_node(state: AgentState) -> Dict[str, Any]:
    """Node: Automatically analyzes language, sentiment, and classifies customer intent."""
    current_message = state["current_message"]
    
    lang = detect_language_heuristics(current_message)
    sentiment = detect_sentiment_heuristics(current_message)
    category = classify_intent_heuristics(current_message)
    
    logger.info(f"Node [Detector] - Lang: {lang}, Sentiment: {sentiment}, Category: {category}")
    
    return {
        "detected_language": lang,
        "detected_sentiment": sentiment,
        "category": category
    }


def greeting_agent_node(state: AgentState) -> Dict[str, Any]:
    """Node: Handles standard greetings in Bangla or English."""
    lang = state["detected_language"]
    
    # Query LLM if available
    llm_resp = query_llm_api(
        prompt=state["current_message"],
        system_prompt=f"You are a friendly customer service greeting agent. Respond warmly in the language of the user (Detected: {lang}). Keep it short."
    )
    
    if llm_resp:
        answer = llm_resp
    else:
        # Fallback responses
        if lang in ["bn", "mixed"]:
            answer = "হ্যালো! আমাদের কাস্টমার সাপোর্ট পোর্টালে আপনাকে স্বাগতম। আজ আপনাকে কীভাবে সাহায্য করতে পারি?"
        else:
            answer = "Hello! Welcome to our customer support portal. How can I assist you today?"
            
    return {
        "answer": answer,
        "confidence_score": 1.0,
        "sources": [],
        "messages": [AIMessage(content=answer)]
    }


def faq_agent_node(state: AgentState) -> Dict[str, Any]:
    """Node: RAG Agent querying vector store and composing synthesized citations."""
    query = state["current_message"]
    lang = state["detected_language"]
    
    # Query vector database
    retrieved_docs = vector_store.query_documents(query, n_results=3)
    
    # Format citations
    sources = []
    context_blocks = []
    
    for idx, doc in enumerate(retrieved_docs):
        src = doc["metadata"].get("source", f"Document-{idx+1}")
        sources.append({
            "id": doc["id"],
            "source": src,
            "confidence": doc["confidence_score"],
            "snippet": doc["content"][:200] + "..."
        })
        context_blocks.append(f"Source: {src}\nContent: {doc['content']}")
        
    combined_context = "\n\n".join(context_blocks)
    
    # Confidence score is the average of retrieved matches (default to 0.0 if empty list)
    confidence = float(np.mean([d["confidence_score"] for d in retrieved_docs])) if retrieved_docs else 0.0
    
    # If confidence is below 0.35, route to automatic escalation
    if confidence < 0.35:
        logger.info(f"RAG confidence ({confidence:.2f}) too low. Redirecting to Escalation.")
        return {
            "confidence_score": confidence,
            "category": "escalation"
        }
        
    llm_prompt = f"Context:\n{combined_context}\n\nQuestion: {query}\n\nProvide an answer strictly using the context above. If you don't know, state it clearly. Language: {lang}."
    llm_resp = query_llm_api(
        prompt=llm_prompt,
        system_prompt="You are a helpful knowledge assistant. Keep your responses accurate and cite sources when necessary."
    )
    
    if llm_resp:
        answer = llm_resp
    else:
        # Structured heuristic fallback
        sources_str = ", ".join([s["source"] for s in sources])
        if lang in ["bn", "mixed"]:
            answer = f"আমাদের নথি অনুসারে: {retrieved_docs[0]['content']}\n\n(উৎস: {sources_str})"
        else:
            answer = f"According to our knowledge base: {retrieved_docs[0]['content']}\n\n(Sources: {sources_str})"
            
    return {
        "answer": answer,
        "confidence_score": confidence,
        "sources": sources,
        "messages": [AIMessage(content=answer)]
    }


def order_support_agent_node(state: AgentState) -> Dict[str, Any]:
    """Node: Handles customer order status lookups and order issues."""
    lang = state["detected_language"]
    msg = state["current_message"]
    
    # Extract order ID format (e.g. #12345 or ORD-987)
    order_match = re.search(r'(#\d+|ord-\d+|\b\d{5}\b)', msg.lower())
    order_id = order_match.group(1).upper() if order_match else None
    
    if order_id:
        if lang in ["bn", "mixed"]:
            answer = f"আমি আপনার অর্ডার {order_id} ট্র্যাক করেছি। এটি বর্তমানে ডেলিভারির জন্য প্রক্রিয়াধীন রয়েছে এবং আগামী ২ কার্যদিবসের মধ্যে আপনার ঠিকানায় পৌঁছাবে।"
        else:
            answer = f"I have successfully tracked your order {order_id}. It is currently in transit and is expected to arrive within the next 2 business days."
    else:
        if lang in ["bn", "mixed"]:
            answer = "অর্ডার স্ট্যাটাস দেখতে অনুগ্রহ করে আপনার ৫ সংখ্যার অর্ডার আইডিটি উল্লেখ করুন (যেমন: #১২৩৪৫)।"
        else:
            answer = "To assist you with your order details, could you please provide your 5-digit Order ID (e.g., #12345)?"
            
    return {
        "answer": answer,
        "confidence_score": 0.9,
        "sources": [],
        "messages": [AIMessage(content=answer)]
    }


def billing_agent_node(state: AgentState) -> Dict[str, Any]:
    """Node: Handles transaction logs, billing errors, and payment issues."""
    lang = state["detected_language"]
    
    if lang in ["bn", "mixed"]:
        answer = "বিলিং এবং পেমেন্ট সংক্রান্ত তথ্যের জন্য: আমরা পেমেন্ট গেটওয়েতে আপনার লেনদেনের ইতিহাস যাচাই করছি। নিশ্চিত থাকুন, কোনো অতিরিক্ত চার্জ নেওয়া হলে তা আগামী ৫-৭ দিনের মধ্যে ফেরত দেওয়া হবে।"
    else:
        answer = "Regarding your billing inquiry: We are verifying your recent transaction logs. Rest assured, any accidental double charges will be fully refunded within 5-7 business days."
        
    return {
        "answer": answer,
        "confidence_score": 0.85,
        "sources": [],
        "messages": [AIMessage(content=answer)]
    }


def complaint_agent_node(state: AgentState) -> Dict[str, Any]:
    """Node: Receives complaints. Triggers priority escalation if sentiment is highly negative."""
    lang = state["detected_language"]
    sentiment = state["detected_sentiment"]
    
    # If customer is angry/negative, automatically update intent to trigger escalation
    if sentiment == "negative":
        logger.info("Complaint sentiment is negative. Rerouting to Escalation Node.")
        return {
            "category": "escalation"
        }
        
    if lang in ["bn", "mixed"]:
        answer = "আমরা আপনার অভিযোগটি গুরুত্বের সাথে নথিভুক্ত করেছি। আমাদের কোয়ালিটি কন্ট্রোল টিম বিষয়টি খতিয়ে দেখছে এবং দ্রুত ব্যবস্থা গ্রহণ করবে।"
    else:
        answer = "We have registered your complaint and log details. Our quality assurance team is investigating the issue to ensure this does not happen again."
        
    return {
        "answer": answer,
        "confidence_score": 0.9,
        "sources": [],
        "messages": [AIMessage(content=answer)]
    }


def escalation_agent_node(state: AgentState) -> Dict[str, Any]:
    """Node: Creates database support ticket automatically and notifies human support agents."""
    lang = state["detected_language"]
    query = state["current_message"]
    sentiment = state["detected_sentiment"]
    
    # Save ticket in the database
    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    
    # Setup DB session
    db = SessionLocal()
    try:
        # Look up admin or assign to system
        agent = db.query(User).filter(User.role == "agent").first()
        agent_id = agent.id if agent else None
        
        ticket = Ticket(
            ticket_id=ticket_id,
            customer_name="Online Customer",
            email="customer@example.com",
            category=state.get("category", "general"),
            priority="high" if sentiment == "negative" else "medium",
            status="open",
            description=query,
            sentiment=sentiment,
            assigned_agent_id=agent_id
        )
        db.add(ticket)
        db.commit()
        logger.info(f"Support ticket {ticket_id} automatically created in DB.")
    except Exception as e:
        logger.error(f"Error saving escalation ticket to DB: {e}")
        db.rollback()
    finally:
        db.close()
        
    # Generate user message response
    if lang in ["bn", "mixed"]:
        answer = f"আমি দুঃখিত যে স্বয়ংক্রিয়ভাবে আমি আপনার সমস্যার সমাধান করতে পারছি না। আমি আপনার জন্য একটি কাস্টমার সাপোর্ট টিকিট তৈরি করেছি (টিকিট আইডি: {ticket_id})। আমাদের একজন কাস্টমার রিপ্রেজেন্টেটিভ শীঘ্রই ইমেইলে আপনার সাথে যোগাযোগ করবেন।"
    else:
        answer = f"I apologize that I couldn't resolve this issue automatically. I have created a priority support ticket for you (Ticket ID: {ticket_id}). One of our human support agents will follow up via email shortly."
        
    return {
        "answer": answer,
        "confidence_score": 1.0,
        "ticket_escalated": True,
        "ticket_id": ticket_id,
        "sources": [],
        "messages": [AIMessage(content=answer)]
    }
