from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
import datetime

# ── Auth ───────────────────────────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    tenant_id: Optional[str] = None

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    tenant_id: Optional[str] = None


# ── Tenant ────────────────────────────────────────────────────────────────────
class TenantCreate(BaseModel):
    name: str
    domain: Optional[str] = None
    plan: Optional[str] = "free"
    widget_color: Optional[str] = "#6366f1"
    welcome_message: Optional[str] = None

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    plan: Optional[str] = None
    widget_color: Optional[str] = None
    welcome_message: Optional[str] = None
    is_active: Optional[bool] = None

class TenantResponse(BaseModel):
    id: str
    name: str
    domain: Optional[str] = None
    api_key: str
    plan: str
    is_active: bool
    widget_color: str
    welcome_message: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}

class TenantStats(BaseModel):
    tenant_id: str
    name: str
    total_tickets: int
    open_tickets: int
    total_conversations: int
    kb_entries: int


# ── User ──────────────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Optional[str] = "customer"
    tenant_id: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    tenant_id: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    tenant_id: Optional[str] = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# ── Message ───────────────────────────────────────────────────────────────────
class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender: str
    content: str
    confidence_score: float
    sources: Optional[str] = None
    timestamp: datetime.datetime

    model_config = {"from_attributes": True}


# ── Conversation ──────────────────────────────────────────────────────────────
class ConversationCreate(BaseModel):
    session_id: str
    title: Optional[str] = None

class ConversationResponse(BaseModel):
    id: int
    session_id: str
    title: Optional[str] = None
    language: str
    sentiment: str
    created_at: datetime.datetime
    messages: List[MessageResponse] = []

    model_config = {"from_attributes": True}


# ── Ticket ────────────────────────────────────────────────────────────────────
class TicketCreate(BaseModel):
    customer_name: str
    email: EmailStr
    category: str
    description: str
    priority: Optional[str] = "medium"

class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_agent_id: Optional[int] = None

class TicketResponse(BaseModel):
    id: int
    ticket_id: str
    tenant_id: Optional[str] = None
    customer_name: str
    email: EmailStr
    category: str
    priority: str
    status: str
    description: str
    sentiment: str
    assigned_agent_id: Optional[int] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


# ── Feedback ──────────────────────────────────────────────────────────────────
class FeedbackCreate(BaseModel):
    session_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    conversation_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# ── Order ─────────────────────────────────────────────────────────────────────
class OrderCreate(BaseModel):
    customer_name: str
    customer_email: EmailStr
    items: List[str]
    total_amount: float
    estimated_delivery: Optional[str] = None

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    estimated_delivery: Optional[str] = None

class OrderResponse(BaseModel):
    id: int
    order_id: str
    customer_name: str
    customer_email: str
    status: str
    items: Optional[str] = None
    total_amount: Optional[float] = None
    estimated_delivery: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


# ── Product ───────────────────────────────────────────────────────────────────
class ProductCreate(BaseModel):
    name: str
    name_bn: Optional[str] = None
    description: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    category: Optional[str] = None
    features: Optional[str] = None   # JSON array string
    in_stock: bool = True

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    name_bn: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    category: Optional[str] = None
    features: Optional[str] = None
    in_stock: Optional[bool] = None

class ProductResponse(BaseModel):
    id: int
    name: str
    name_bn: Optional[str] = None
    description: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    category: Optional[str] = None
    features: Optional[str] = None
    in_stock: bool
    tenant_id: Optional[str] = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# ── Knowledge ─────────────────────────────────────────────────────────────────
class KnowledgeDocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    status: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}

class KnowledgeEntryCreate(BaseModel):
    question: str
    answer: str
    category: Optional[str] = "general"

class KnowledgeEntryResponse(BaseModel):
    id: int
    tenant_id: str
    question: str
    answer: str
    category: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# ── Analytics ─────────────────────────────────────────────────────────────────
class AnalyticsSummaryResponse(BaseModel):
    total_conversations: int
    total_tickets: int
    avg_response_time_seconds: float
    resolution_rate: float
    user_satisfaction_avg: float
    frequent_faqs: List[dict]
    sentiment_distribution: dict
    language_distribution: dict

class DailyDataPoint(BaseModel):
    date: str
    conversations: int
    tickets: int
    feedback_avg: float

class AnalyticsChartsResponse(BaseModel):
    daily_stats: List[DailyDataPoint]
    sentiment_data: List[dict]
    language_data: List[dict]
