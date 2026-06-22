import asyncio
import io
import json
import logging
import datetime
import os
import uuid
import httpx
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from langchain_core.messages import HumanMessage, AIMessage

from app.config import settings
from app.database import get_db
from app.models import User, Ticket, Conversation, Message, Feedback, KnowledgeDocument, Order, Tenant, KnowledgeEntry, Product
from app.schemas import (
    UserCreate, UserUpdate, UserResponse, Token, TicketCreate, TicketResponse,
    TicketUpdate, FeedbackCreate, FeedbackResponse, AnalyticsSummaryResponse,
    AnalyticsChartsResponse, DailyDataPoint,
    OrderCreate, OrderUpdate, OrderResponse,
    TenantCreate, TenantUpdate, TenantResponse, TenantStats,
    KnowledgeEntryCreate, KnowledgeEntryResponse,
    ProductCreate, ProductUpdate, ProductResponse,
)
from app.auth import (
    get_password_hash, verify_password, create_access_token,
    get_current_user, get_current_active_user,
    require_admin, require_agent_or_admin,
    require_super_admin, require_store_admin,
    get_tenant_from_api_key,
)
from app.agents.graph import support_graph
from app.agents.nodes import detect_sentiment_heuristics
from app.rag.ingestion import document_ingestor

logger = logging.getLogger(__name__)

# ── Prometheus metrics ────────────────────────────────────────────────────────
from prometheus_client import Counter, Histogram, Gauge

chat_requests_total = Counter(
    "chat_requests_total", "Total chat messages received", ["language", "sentiment"]
)
chat_latency_seconds = Histogram(
    "chat_latency_seconds", "Chat endpoint response time in seconds",
    buckets=[0.5, 1, 2, 5, 10, 30]
)
tickets_created_total = Counter(
    "tickets_created_total", "Total support tickets created", ["status"]
)
active_conversations = Gauge(
    "active_conversations_total", "Number of distinct conversation sessions"
)
orders_placed_total = Counter(
    "orders_placed_total", "Total orders placed"
)
# ─────────────────────────────────────────────────────────────────────────────

# Create main router
api_router = APIRouter()

# ----------------------------------------------------
# 1. AUTHENTICATION ENDPOINTS
# ----------------------------------------------------

@api_router.post("/auth/register", response_model=UserResponse)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new customer, agent, or administrator."""
    db_user = db.query(User).filter(User.email == user_in.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email address already exists."
        )
    
    hashed_pw = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_pw,
        full_name=user_in.full_name,
        role=user_in.role or "customer",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@api_router.post("/auth/token", response_model=Token)
def login_for_access_token(
    username: str = Form(...),  # OAuth2 password flow uses username
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Authenticate email and password credentials, returning a signed JWT access token."""
    user = db.query(User).filter(User.email == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={
        "sub": user.email,
        "role": user.role,
        "tenant_id": user.tenant_id,
    })
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "tenant_id": user.tenant_id,
    }

@api_router.get("/auth/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Retrieve details for the currently authenticated account."""
    return current_user


# ----------------------------------------------------
# 2. CHAT & WEBSOCKET ENDPOINTS
# ----------------------------------------------------

class ConnectionManager:
    """Manages active real-time WebSocket client connections."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

manager = ConnectionManager()

@api_router.post("/chat")
def chat_rest(
    message_in: str = Form(...),
    session_id: str = Form(...),
    preferred_language: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Synchronous HTTP REST endpoint to execute the agent.
    Runs a single turn and stores conversation records.
    """
    # 1. Resolve conversation
    conv = db.query(Conversation).filter(Conversation.session_id == session_id).first()
    if not conv:
        conv = Conversation(session_id=session_id, title=message_in[:40] + "...")
        db.add(conv)
        db.commit()
        db.refresh(conv)
        
    # 2. Load conversation history (SQL-side LIMIT avoids loading all rows)
    history = []
    recent_msgs = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.id.desc()).limit(10).all()
    for msg in reversed(recent_msgs):
        if msg.sender == "user":
            history.append(HumanMessage(content=msg.content))
        else:
            history.append(AIMessage(content=msg.content))
            
    # 3. Invoke LangGraph
    state_input = {
        "messages": history,
        "current_message": message_in,
        "session_id": session_id,
        "preferred_language": preferred_language if preferred_language in ("bn", "en") else None,
        "ticket_escalated": False,
        "ticket_id": None,
        "answer": "",
        "confidence_score": 1.0,
        "sources": []
    }
    
    with chat_latency_seconds.time():
        graph_output = support_graph.invoke(state_input)

    # Extract outcomes
    answer = graph_output.get("answer", "I couldn't process this.")
    confidence = graph_output.get("confidence_score", 1.0)
    sources = graph_output.get("sources", [])
    lang = graph_output.get("detected_language", "en")
    sentiment = graph_output.get("detected_sentiment", "neutral")
    ticket_escalated = graph_output.get("ticket_escalated", False)
    tkt_id = graph_output.get("ticket_id", None)

    chat_requests_total.labels(language=lang, sentiment=sentiment).inc()
    active_conversations.set(db.query(Conversation).count())
    
    # 4. Save to Database
    user_msg = Message(conversation_id=conv.id, sender="user", content=message_in)
    bot_msg = Message(
        conversation_id=conv.id, 
        sender="bot", 
        content=answer, 
        confidence_score=confidence,
        sources=json.dumps(sources)
    )
    conv.language = lang
    conv.sentiment = sentiment
    db.add_all([user_msg, bot_msg])
    db.commit()
    
    return {
        "answer": answer,
        "confidence_score": confidence,
        "sources": sources,
        "language": lang,
        "sentiment": sentiment,
        "ticket_escalated": ticket_escalated,
        "ticket_id": tkt_id
    }


@api_router.websocket("/chat/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, db: Session = Depends(get_db)):
    """WebSocket handler driving dynamic multi-turn interactions with agent state preservation."""
    await manager.connect(websocket)
    try:
        # Resolve/Create conversation
        conv = db.query(Conversation).filter(Conversation.session_id == session_id).first()
        if not conv:
            conv = Conversation(session_id=session_id, title="WebSocket Chat")
            db.add(conv)
            db.commit()
            db.refresh(conv)
            
        while True:
            # Receive client text
            data = await websocket.receive_text()
            payload = json.loads(data)
            user_text = payload.get("message", "").strip()
            
            if not user_text:
                continue
                
            # Fetch history (SQL-side LIMIT avoids loading all rows)
            history = []
            recent_msgs = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.id.desc()).limit(10).all()
            for msg in reversed(recent_msgs):
                if msg.sender == "user":
                    history.append(HumanMessage(content=msg.content))
                else:
                    history.append(AIMessage(content=msg.content))

            # Invoke LangGraph workflow (run_in_executor keeps blocking httpx off the event loop)
            state_input = {
                "messages": history,
                "current_message": user_text,
                "session_id": session_id,
                "ticket_escalated": False,
                "ticket_id": None,
                "answer": "",
                "confidence_score": 1.0,
                "sources": []
            }

            loop = asyncio.get_event_loop()
            graph_output = await loop.run_in_executor(None, support_graph.invoke, state_input)
            
            answer = graph_output.get("answer", "")
            confidence = graph_output.get("confidence_score", 1.0)
            sources = graph_output.get("sources", [])
            lang = graph_output.get("detected_language", "en")
            sentiment = graph_output.get("detected_sentiment", "neutral")
            ticket_escalated = graph_output.get("ticket_escalated", False)
            tkt_id = graph_output.get("ticket_id", None)
            
            # Save turns to database
            user_msg = Message(conversation_id=conv.id, sender="user", content=user_text)
            bot_msg = Message(
                conversation_id=conv.id,
                sender="bot",
                content=answer,
                confidence_score=confidence,
                sources=json.dumps(sources)
            )
            conv.language = lang
            conv.sentiment = sentiment
            db.add_all([user_msg, bot_msg])
            db.commit()
            
            # Return JSON structure back over WebSocket
            await websocket.send_text(json.dumps({
                "answer": answer,
                "confidence_score": confidence,
                "sources": sources,
                "language": lang,
                "sentiment": sentiment,
                "ticket_escalated": ticket_escalated,
                "ticket_id": tkt_id
            }))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket session {session_id} disconnected.")
    except Exception as e:
        logger.error(f"WebSocket loop error for session {session_id}: {e}")
        manager.disconnect(websocket)


# ----------------------------------------------------
# 3. TICKETING ENDPOINTS
# ----------------------------------------------------

@api_router.post("/tickets", response_model=TicketResponse)
def create_ticket(ticket_in: TicketCreate, db: Session = Depends(get_db)):
    """Manually register a support ticket."""
    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    
    # Analyze sentiment of description
    sentiment = detect_sentiment_heuristics(ticket_in.description)
    priority = ticket_in.priority or "medium"
    
    if sentiment == "negative":
        priority = "urgent"  # Escalate priority automatically for angry feedback
        
    ticket = Ticket(
        ticket_id=ticket_id,
        customer_name=ticket_in.customer_name,
        email=ticket_in.email,
        category=ticket_in.category,
        priority=priority,
        status="open",
        description=ticket_in.description,
        sentiment=sentiment
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    tickets_created_total.labels(status="open").inc()
    return ticket

@api_router.get("/tickets", response_model=List[TicketResponse])
def list_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_agent_or_admin)
):
    """Retrieve tickets scoped to the user's tenant (super_admin sees all)."""
    query = db.query(Ticket)
    # Store admins and agents see their tenant's tickets + unscoped tickets (tenant_id IS NULL)
    if current_user.role in ("store_admin", "agent") and current_user.tenant_id:
        query = query.filter(
            (Ticket.tenant_id == current_user.tenant_id) | (Ticket.tenant_id == None)
        )
    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)
    return query.order_by(Ticket.created_at.desc()).all()

@api_router.put("/tickets/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: str,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_agent_or_admin)
):
    """Modify ticket details, assign agents, or close statuses (Protected: Agents and Admins only)."""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    if ticket_update.status:
        ticket.status = ticket_update.status
    if ticket_update.priority:
        ticket.priority = ticket_update.priority
    if ticket_update.assigned_agent_id is not None:
        ticket.assigned_agent_id = ticket_update.assigned_agent_id
        
    db.commit()
    db.refresh(ticket)
    return ticket


# ----------------------------------------------------
# 4. FEEDBACK ENDPOINTS
# ----------------------------------------------------

@api_router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(feedback_in: FeedbackCreate, db: Session = Depends(get_db)):
    """Log customer review score (1-5) and additional remarks for a specific chat session."""
    conv = db.query(Conversation).filter(Conversation.session_id == feedback_in.session_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation session not found")
        
    fb = Feedback(
        conversation_id=conv.id,
        rating=feedback_in.rating,
        comment=feedback_in.comment
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb


# ----------------------------------------------------
# 5. ORDER MANAGEMENT ENDPOINTS
# ----------------------------------------------------

@api_router.post("/orders", response_model=OrderResponse)
def create_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_agent_or_admin)
):
    """Create a new order record."""
    import json as _json
    order_id = f"ORD-{uuid.uuid4().hex[:5].upper()}"
    order = Order(
        order_id=order_id,
        customer_name=order_in.customer_name,
        customer_email=order_in.customer_email,
        status="processing",
        items=_json.dumps(order_in.items),
        total_amount=order_in.total_amount,
        estimated_delivery=order_in.estimated_delivery
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@api_router.get("/orders", response_model=List[OrderResponse])
def list_orders(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_agent_or_admin)
):
    """List all orders, optionally filtered by status."""
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    return query.order_by(Order.created_at.desc()).all()


@api_router.post("/orders/place", response_model=OrderResponse)
def place_order_public(order_in: OrderCreate, db: Session = Depends(get_db)):
    """Public order placement — no authentication required. Used by the ecommerce storefront."""
    import json as _json
    order_id = f"ORD-{uuid.uuid4().hex[:5].upper()}"
    order = Order(
        order_id=order_id,
        customer_name=order_in.customer_name,
        customer_email=order_in.customer_email,
        status="processing",
        items=_json.dumps(order_in.items),
        total_amount=order_in.total_amount,
        estimated_delivery=order_in.estimated_delivery,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    orders_placed_total.inc()
    logger.info(f"Public order placed: {order_id} for {order_in.customer_name}")
    return order


@api_router.get("/orders/track/{order_id}")
def track_order_public(order_id: str, db: Session = Depends(get_db)):
    """Public order status lookup — no authentication required."""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "order_id": order.order_id,
        "status": order.status,
        "customer_name": order.customer_name,
        "estimated_delivery": order.estimated_delivery,
        "total_amount": order.total_amount,
        "items": order.items,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }


@api_router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_agent_or_admin)
):
    """Retrieve a single order by its order_id."""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@api_router.put("/orders/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: str,
    order_update: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_agent_or_admin)
):
    """Update order status or estimated delivery."""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order_update.status:
        order.status = order_update.status
    if order_update.estimated_delivery is not None:
        order.estimated_delivery = order_update.estimated_delivery
    db.commit()
    db.refresh(order)
    return order


@api_router.delete("/orders/{order_id}")
def delete_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete an order (Admin only)."""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(order)
    db.commit()
    return {"detail": f"Order {order_id} deleted."}


# ----------------------------------------------------
# 6. KNOWLEDGE FILE UPLOADS
# ----------------------------------------------------

@api_router.post("/upload")
def upload_knowledge_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Upload PDF, DOCX, CSV, or TXT documentation to seed the vector base (Protected: Admins only)."""
    # Create scratch folder locally inside workspace to buffer uploads
    upload_dir = "./uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())
            
        # Register document status
        doc = KnowledgeDocument(
            filename=file.filename,
            file_type=file.filename.split('.')[-1].upper(),
            file_path=file_path,
            status="pending"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        # Ingest text chunks into vector store
        num_chunks = document_ingestor.ingest_file(file_path, file.filename)
        
        doc.status = "processed"
        db.commit()
        
        return {
            "message": "File uploaded and processed successfully",
            "filename": file.filename,
            "chunks_created": num_chunks,
            "document_id": doc.id
        }
    except Exception as e:
        logger.error(f"Failed processing file upload: {e}")
        # Mark db entry as failed if exists
        try:
            doc.status = "failed"
            db.commit()
        except:
            pass
        raise HTTPException(status_code=500, detail=f"File ingestion error: {str(e)}")


# ----------------------------------------------------
# 6. ADMIN ANALYTICS DASHBOARDS
# ----------------------------------------------------

@api_router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """Fetch high-level business analytics, FAQs, and ticket resolution statistics (Protected: Admins only)."""
    total_convs = db.query(func.count(Conversation.id)).scalar() or 0
    total_tickets = db.query(func.count(Ticket.id)).scalar() or 0
    
    # Average rating from feedback
    avg_rating = db.query(func.avg(Feedback.rating)).scalar() or 4.2
    
    # Resolution Rate (Resolved/Closed tickets vs total)
    resolved_count = db.query(func.count(Ticket.id)).filter(Ticket.status.in_(["resolved", "closed"])).scalar() or 0
    resolution_rate = float(resolved_count / total_tickets) if total_tickets > 0 else 1.0
    
    # Sentiment distribution
    sentiments = db.query(Conversation.sentiment, func.count(Conversation.id)).group_by(Conversation.sentiment).all()
    sentiment_dist = {s[0]: s[1] for s in sentiments} if sentiments else {"neutral": 0, "positive": 0, "negative": 0}
    
    # Language distribution
    languages = db.query(Conversation.language, func.count(Conversation.id)).group_by(Conversation.language).all()
    lang_dist = {l[0]: l[1] for l in languages} if languages else {"bn": 0, "en": 0, "mixed": 0}
    
    # Dummy mock frequent FAQs (Normally extracted by grouping messages)
    frequent_faqs = [
        {"question": "অর্ডার ডেলিভারিতে কত সময় লাগবে?", "count": 25},
        {"question": "পেমেন্ট ফেরত পাওয়ার উপায় কী?", "count": 18},
        {"question": "সরাসরি এজেন্টের সাথে কথা বলতে চাই।", "count": 14}
    ]
    
    return {
        "total_conversations": total_convs,
        "total_tickets": total_tickets,
        "avg_response_time_seconds": 1.45,  # Mock API response time
        "resolution_rate": float(resolution_rate),
        "user_satisfaction_avg": float(avg_rating),
        "frequent_faqs": frequent_faqs,
        "sentiment_distribution": sentiment_dist,
        "language_distribution": lang_dist
    }


@api_router.get("/analytics/charts", response_model=AnalyticsChartsResponse)
def get_analytics_charts(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """Retrieve history series datasets to plot Recharts admin visual charts (Protected: Admins only)."""
    # Build 7 days of daily trends
    daily_stats = []
    base = datetime.date.today()
    for i in range(7):
        date_str = (base - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        daily_stats.append(
            DailyDataPoint(
                date=date_str,
                conversations=15 + (i * 3) % 7,
                tickets=2 + (i * 2) % 4,
                feedback_avg=4.0 + (i * 0.1) % 0.9
            )
        )
    daily_stats.reverse()
    
    # Pie charts aggregates
    sentiment_data = [
        {"name": "Positive", "value": 45, "color": "#10B981"},
        {"name": "Neutral", "value": 30, "color": "#F59E0B"},
        {"name": "Negative", "value": 25, "color": "#EF4444"}
    ]
    
    language_data = [
        {"name": "Bangla", "value": 55, "color": "#3B82F6"},
        {"name": "English", "value": 25, "color": "#8B5CF6"},
        {"name": "Mixed (Banglish)", "value": 20, "color": "#EC4899"}
    ]
    
    return {
        "daily_stats": daily_stats,
        "sentiment_data": sentiment_data,
        "language_data": language_data
    }


# ----------------------------------------------------
# 7. VOICE PROCESSING SERVICES
# ----------------------------------------------------

@api_router.post("/voice/stt")
def speech_to_text(
    file: UploadFile = File(...),
):
    """
    Translate customer vocal audio streams to text strings.
    If SpeechRecognition package is present, it will run transcription,
    otherwise returns a mock translation for testing.
    """
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        
        # Read file bytes
        file_bytes = file.file.read()
        audio_file = io.BytesIO(file_bytes)
        
        # Open as speech source
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            # Try transcribing with Google (supports Bangla 'bn-BD' and English)
            try:
                text = recognizer.recognize_google(audio_data, language="bn-BD")
            except:
                text = recognizer.recognize_google(audio_data, language="en-US")
                
            return {"transcription": text, "status": "success"}
    except Exception as e:
        logger.warning(f"Native audio STT failed or dependencies missing: {e}. Returning fallback transcription.")
        return {
            "transcription": "আমার বিলিং সমস্যা আছে এবং টিকিট খুলতে চাই।", 
            "status": "mocked_success"
        }


@api_router.post("/voice/tts")
def text_to_speech(
    text: str = Form(...),
    lang: str = Form("bn"),
):
    """
    Convert text strings to high-fidelity audio mp3 streaming audio downloads.
    Uses gTTS (Google Text-to-Speech) which is fully cloud-run and robust.
    """
    try:
        from gtts import gTTS
        
        # Map languages
        gt_lang = "bn" if lang in ["bn", "mixed"] else "en"
        
        # Generate speech bytes using gTTS
        tts = gTTS(text=text, lang=gt_lang)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        return StreamingResponse(fp, media_type="audio/mp3", headers={
            "Content-Disposition": "attachment; filename=speech.mp3"
        })
    except Exception as e:
        logger.error(f"Error executing Text-to-Speech: {e}")
        # Return a tiny blank silence MP3 stream on failure to avoid server crashes
        blank_mp3 = b'\xff\xf3\x44\xc4\x00\x00\x00\x03\x48\x00\x00\x00\x00\x4c\x41\x4d\x45\x33\x2e\x39\x39\x72\x00\x00\x00\x00\x00\x00\x00\x00'
        return StreamingResponse(io.BytesIO(blank_mp3), media_type="audio/mp3")


# ----------------------------------------------------
# 8. TELEGRAM BOT INTEGRATION
# ----------------------------------------------------

def _send_telegram_message(chat_id: int, text: str) -> None:
    """Send a text message back to a Telegram chat."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not set — cannot send Telegram reply.")
        return
    try:
        httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10
        )
    except Exception as e:
        logger.error(f"Failed to send Telegram message to {chat_id}: {e}")


def _run_chat_for_telegram(user_text: str, session_id: str, db: Session) -> str:
    """Run the LangGraph agent for a Telegram message and persist to DB."""
    conv = db.query(Conversation).filter(Conversation.session_id == session_id).first()
    if not conv:
        conv = Conversation(session_id=session_id, title=user_text[:40])
        db.add(conv)
        db.commit()
        db.refresh(conv)

    history = []
    recent = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.id.desc()).limit(10).all()
    for msg in reversed(recent):
        if msg.sender == "user":
            history.append(HumanMessage(content=msg.content))
        else:
            history.append(AIMessage(content=msg.content))

    state_input = {
        "messages": history,
        "current_message": user_text,
        "session_id": session_id,
        "ticket_escalated": False,
        "ticket_id": None,
        "answer": "",
        "confidence_score": 1.0,
        "sources": []
    }
    output = support_graph.invoke(state_input)

    answer = output.get("answer", "দুঃখিত, আমি এই মুহূর্তে উত্তর দিতে পারছি না।")
    lang = output.get("detected_language", "en")
    sentiment = output.get("detected_sentiment", "neutral")

    db.add(Message(conversation_id=conv.id, sender="user", content=user_text))
    db.add(Message(
        conversation_id=conv.id, sender="bot", content=answer,
        confidence_score=output.get("confidence_score", 1.0),
        sources=json.dumps(output.get("sources", []))
    ))
    conv.language = lang
    conv.sentiment = sentiment
    db.commit()

    if output.get("ticket_escalated") and output.get("ticket_id"):
        answer += f"\n\n🎫 Ticket ID: {output['ticket_id']}"

    return answer


@api_router.post("/telegram/webhook")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Telegram Bot webhook endpoint.
    Register this URL with Telegram via /telegram/set-webhook or BotFather.
    Requires TELEGRAM_BOT_TOKEN in environment/.env.
    """
    try:
        update = await request.json()
    except Exception:
        return {"ok": True}

    message = update.get("message") or update.get("edited_message")
    if not message:
        return {"ok": True}

    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if not text:
        _send_telegram_message(chat_id, "শুধুমাত্র টেক্সট মেসেজ পাঠান। (Please send text messages only.)")
        return {"ok": True}

    # /start command — welcome message
    if text == "/start":
        _send_telegram_message(
            chat_id,
            "হ্যালো! আমি Bangla AI Customer Support Bot। বাংলা বা ইংরেজিতে আপনার প্রশ্ন লিখুন।\n\n"
            "Hello! I am Bangla AI Customer Support Bot. Ask me anything in Bangla or English."
        )
        return {"ok": True}

    session_id = f"telegram-{chat_id}"
    loop = asyncio.get_event_loop()
    answer = await loop.run_in_executor(None, _run_chat_for_telegram, text, session_id, db)
    _send_telegram_message(chat_id, answer)
    return {"ok": True}


@api_router.post("/telegram/set-webhook")
def set_telegram_webhook(
    webhook_url: str = Form(...),
    current_user: User = Depends(require_admin)
):
    """
    Register a public HTTPS URL as the Telegram webhook (Admin only).
    Example webhook_url: https://yourdomain.com/api/telegram/webhook
    """
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise HTTPException(status_code=400, detail="TELEGRAM_BOT_TOKEN is not configured.")
    try:
        res = httpx.post(
            f"https://api.telegram.org/bot{token}/setWebhook",
            json={"url": webhook_url},
            timeout=10
        )
        return res.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/telegram/webhook-info")
def get_telegram_webhook_info(current_user: User = Depends(require_admin)):
    """Check the currently registered Telegram webhook URL (Admin only)."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise HTTPException(status_code=400, detail="TELEGRAM_BOT_TOKEN is not configured.")
    try:
        res = httpx.get(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=10)
        return res.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------
# 9. PRODUCT ENDPOINTS
# ----------------------------------------------------

@api_router.get("/products", response_model=List[ProductResponse])
def list_products(
    category: Optional[str] = None,
    in_stock: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """Public: list all products, optionally filtered by category or stock."""
    q = db.query(Product)
    if category:
        q = q.filter(Product.category == category)
    if in_stock is not None:
        q = q.filter(Product.in_stock == in_stock)
    return q.order_by(Product.id).all()


@api_router.post("/products", response_model=ProductResponse)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """store_admin / super_admin: create a product."""
    if current_user.role not in ("store_admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Store admin required")
    tenant_id = current_user.tenant_id if current_user.role == "store_admin" else None
    product = Product(**product_in.model_dump(), tenant_id=tenant_id)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@api_router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """store_admin / super_admin: update a product."""
    if current_user.role not in ("store_admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Store admin required")
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in product_in.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@api_router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """store_admin / super_admin: delete a product."""
    if current_user.role not in ("store_admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Store admin required")
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"ok": True}


# ----------------------------------------------------
# 10. TELEMETRY PROMETHEUS METRICS
# ----------------------------------------------------
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

@api_router.get("/metrics")
def get_metrics():
    """Expose Prometheus telemetry logs."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ============================================================
# 10. TENANT MANAGEMENT  (super_admin only)
# ============================================================

def _generate_api_key() -> str:
    return "sk_" + uuid.uuid4().hex[:32]

@api_router.post("/tenants", response_model=TenantResponse)
def create_tenant(
    payload: TenantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Create a new ecommerce tenant / store account."""
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name=payload.name,
        domain=payload.domain,
        api_key=_generate_api_key(),
        plan=payload.plan or "free",
        widget_color=payload.widget_color or "#6366f1",
        welcome_message=payload.welcome_message or "হ্যালো! কীভাবে সাহায্য করতে পারি?",
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant

@api_router.get("/tenants", response_model=List[TenantResponse])
def list_tenants(db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    """List all registered tenants."""
    return db.query(Tenant).order_by(Tenant.created_at.desc()).all()

@api_router.get("/tenants/{tenant_id}", response_model=TenantResponse)
def get_tenant(tenant_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return t

@api_router.put("/tenants/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    tenant_id: str,
    payload: TenantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    for field, val in payload.model_dump(exclude_none=True).items():
        setattr(t, field, val)
    db.commit()
    db.refresh(t)
    return t

@api_router.delete("/tenants/{tenant_id}")
def delete_tenant(tenant_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    db.delete(t)
    db.commit()
    return {"detail": f"Tenant '{t.name}' deleted."}

@api_router.post("/tenants/{tenant_id}/rotate-key", response_model=TenantResponse)
def rotate_api_key(tenant_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    """Generate a new API key for a tenant (invalidates the old one)."""
    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    t.api_key = _generate_api_key()
    db.commit()
    db.refresh(t)
    return t

@api_router.get("/tenants/{tenant_id}/stats", response_model=TenantStats)
def get_tenant_stats(tenant_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return TenantStats(
        tenant_id=t.id,
        name=t.name,
        total_tickets=db.query(func.count(Ticket.id)).filter(Ticket.tenant_id == tenant_id).scalar() or 0,
        open_tickets=db.query(func.count(Ticket.id)).filter(Ticket.tenant_id == tenant_id, Ticket.status == "open").scalar() or 0,
        total_conversations=db.query(func.count(Conversation.id)).filter(Conversation.tenant_id == tenant_id).scalar() or 0,
        kb_entries=db.query(func.count(KnowledgeEntry.id)).filter(KnowledgeEntry.tenant_id == tenant_id).scalar() or 0,
    )

# Users — super admin can list and manage all platform users
@api_router.get("/users", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_super_admin)):
    return db.query(User).order_by(User.created_at.desc()).all()

@api_router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field, val in payload.model_dump(exclude_none=True).items():
        setattr(user, field, val)
    db.commit()
    db.refresh(user)
    return user


# ============================================================
# 11. STORE ADMIN SELF-SERVICE  (store_admin scoped)
# ============================================================

@api_router.get("/my-store", response_model=TenantResponse)
def get_my_store(db: Session = Depends(get_db), current_user: User = Depends(require_store_admin)):
    """Return the store details for the currently logged-in store admin."""
    if current_user.role == "super_admin":
        raise HTTPException(status_code=400, detail="super_admin has no single store — use /tenants")
    t = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="No store associated with this account")
    return t

@api_router.put("/my-store", response_model=TenantResponse)
def update_my_store(
    payload: TenantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store_admin),
):
    if current_user.role == "super_admin":
        raise HTTPException(status_code=400, detail="Use /tenants/{id} for super_admin")
    t = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="No store found")
    for field, val in payload.model_dump(exclude_none=True).items():
        setattr(t, field, val)
    db.commit()
    db.refresh(t)
    return t

@api_router.get("/my-store/embed-code")
def get_embed_code(db: Session = Depends(get_db), current_user: User = Depends(require_store_admin)):
    """Return the HTML embed snippet for this store's chatbot widget."""
    if current_user.role == "super_admin":
        raise HTTPException(status_code=400, detail="Use /tenants/{id} for super_admin")
    t = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="No store found")
    snippet = f"""<!-- ChatBot Widget — paste before </body> on your website -->
<script>
  window.SHOPBOT_KEY  = "{t.api_key}";
  window.SHOPBOT_API  = "https://your-platform-domain.com";
  window.SHOPBOT_COLOR = "{t.widget_color}";
</script>
<script src="https://your-platform-domain.com/api/widget.js" async></script>"""
    return {"api_key": t.api_key, "embed_snippet": snippet, "widget_color": t.widget_color}


# ── Knowledge Base Management ─────────────────────────────────────────────────

@api_router.get("/my-store/knowledge", response_model=List[KnowledgeEntryResponse])
def list_kb_entries(db: Session = Depends(get_db), current_user: User = Depends(require_store_admin)):
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="No store associated")
    return db.query(KnowledgeEntry).filter(KnowledgeEntry.tenant_id == current_user.tenant_id).order_by(KnowledgeEntry.id.desc()).all()

@api_router.post("/my-store/knowledge", response_model=KnowledgeEntryResponse)
def create_kb_entry(
    payload: KnowledgeEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store_admin),
):
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="No store associated")
    entry = KnowledgeEntry(
        tenant_id=current_user.tenant_id,
        question=payload.question,
        answer=payload.answer,
        category=payload.category or "general",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    # Index into vector store with tenant scoping
    try:
        from app.rag.vectorstore import vector_store
        text = f"Q: {payload.question}\nA: {payload.answer}"
        vid = str(uuid.uuid4())
        vector_store.add_documents(
            [text],
            [{"tenant_id": current_user.tenant_id, "source": "store_kb", "category": payload.category or "general"}],
            [vid],
        )
        entry.vector_id = vid
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to index KB entry into vector store: {e}")
    return entry

@api_router.delete("/my-store/knowledge/{entry_id}")
def delete_kb_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store_admin),
):
    entry = db.query(KnowledgeEntry).filter(
        KnowledgeEntry.id == entry_id,
        KnowledgeEntry.tenant_id == current_user.tenant_id,
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(entry)
    db.commit()
    return {"detail": "Deleted"}


# ── Agent Management (by store admin) ────────────────────────────────────────

@api_router.get("/my-store/agents", response_model=List[UserResponse])
def list_store_agents(db: Session = Depends(get_db), current_user: User = Depends(require_store_admin)):
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="No store associated")
    return db.query(User).filter(
        User.tenant_id == current_user.tenant_id,
        User.role == "agent",
    ).all()

@api_router.post("/my-store/agents", response_model=UserResponse)
def add_agent(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store_admin),
):
    """Register a new support agent and assign them to this store."""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="No store associated")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    agent = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        role="agent",
        tenant_id=current_user.tenant_id,
        is_active=True,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent

@api_router.delete("/my-store/agents/{user_id}")
def remove_agent(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store_admin),
):
    agent = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == current_user.tenant_id,
        User.role == "agent",
    ).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found in your store")
    db.delete(agent)
    db.commit()
    return {"detail": "Agent removed"}


# ── Store analytics ───────────────────────────────────────────────────────────

@api_router.get("/my-store/stats")
def get_my_store_stats(db: Session = Depends(get_db), current_user: User = Depends(require_store_admin)):
    tid = current_user.tenant_id
    if not tid:
        raise HTTPException(status_code=400, detail="No store associated")
    return {
        "total_tickets":   db.query(func.count(Ticket.id)).filter(Ticket.tenant_id == tid).scalar() or 0,
        "open_tickets":    db.query(func.count(Ticket.id)).filter(Ticket.tenant_id == tid, Ticket.status == "open").scalar() or 0,
        "conversations":   db.query(func.count(Conversation.id)).filter(Conversation.tenant_id == tid).scalar() or 0,
        "kb_entries":      db.query(func.count(KnowledgeEntry.id)).filter(KnowledgeEntry.tenant_id == tid).scalar() or 0,
        "agents":          db.query(func.count(User.id)).filter(User.tenant_id == tid, User.role == "agent").scalar() or 0,
    }


# ============================================================
# 12. WIDGET API  (API-key auth — for embedded storefronts)
# ============================================================

@api_router.get("/widget/config")
def widget_config(tenant: Tenant = Depends(get_tenant_from_api_key)):
    """Return widget display config (color, welcome message) for a store's embed."""
    return {
        "store_name":       tenant.name,
        "widget_color":     tenant.widget_color,
        "welcome_message":  tenant.welcome_message,
    }

@api_router.post("/widget/chat")
def widget_chat(
    message_in: str = Form(...),
    session_id: str = Form(...),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant_from_api_key),
):
    """Chat endpoint for embedded widgets — authenticated via X-Api-Key header."""
    conv = db.query(Conversation).filter(Conversation.session_id == session_id).first()
    if not conv:
        conv = Conversation(session_id=session_id, title=message_in[:40] + "...", tenant_id=tenant.id)
        db.add(conv)
        db.commit()
        db.refresh(conv)

    history = []
    recent_msgs = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.id.desc()).limit(10).all()
    for msg in reversed(recent_msgs):
        history.append(HumanMessage(content=msg.content) if msg.sender == "user" else AIMessage(content=msg.content))

    state_input = {
        "messages": history,
        "current_message": message_in,
        "session_id": session_id,
        "tenant_id": tenant.id,
        "ticket_escalated": False,
        "ticket_id": None,
        "answer": "",
        "confidence_score": 1.0,
        "sources": [],
    }
    graph_output = support_graph.invoke(state_input)

    answer           = graph_output.get("answer", "")
    confidence       = graph_output.get("confidence_score", 1.0)
    sources          = graph_output.get("sources", [])
    lang             = graph_output.get("detected_language", "en")
    sentiment        = graph_output.get("detected_sentiment", "neutral")
    ticket_escalated = graph_output.get("ticket_escalated", False)
    tkt_id           = graph_output.get("ticket_id", None)

    # Tag tickets with tenant
    if ticket_escalated and tkt_id:
        db.query(Ticket).filter(Ticket.ticket_id == tkt_id).update({"tenant_id": tenant.id})

    db.add(Message(conversation_id=conv.id, sender="user", content=message_in))
    db.add(Message(conversation_id=conv.id, sender="bot", content=answer,
                   confidence_score=confidence, sources=json.dumps(sources)))
    conv.language = lang
    conv.sentiment = sentiment
    db.commit()

    return {
        "answer": answer,
        "confidence_score": confidence,
        "sources": sources,
        "language": lang,
        "sentiment": sentiment,
        "ticket_escalated": ticket_escalated,
        "ticket_id": tkt_id,
    }

