from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
import datetime

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None


# --- User Schemas ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Optional[str] = "customer"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# --- Message Schemas ---
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


# --- Conversation Schemas ---
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


# --- Ticket Schemas ---
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


# --- Feedback Schemas ---
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


# --- Document Schemas ---
class KnowledgeDocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    status: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# --- Analytics Schemas ---
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
