import uuid
import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Tenant(Base):
    """A registered ecommerce store that has integrated the chatbot."""
    __tablename__ = "tenants"

    id           = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name         = Column(String(255), nullable=False)
    domain       = Column(String(255), nullable=True)
    api_key      = Column(String(64), unique=True, nullable=False, index=True)
    plan         = Column(String(50), default="free")       # free | pro | enterprise
    is_active    = Column(Boolean, default=True)
    widget_color = Column(String(20), default="#6366f1")
    welcome_message = Column(Text, default="হ্যালো! কীভাবে সাহায্য করতে পারি? (Hello! How can I help?)")
    created_at   = Column(DateTime, default=datetime.datetime.utcnow)

    users         = relationship("User",          foreign_keys="[User.tenant_id]",         back_populates="tenant")
    tickets       = relationship("Ticket",        back_populates="tenant")
    conversations = relationship("Conversation",  back_populates="tenant")
    kb_entries    = relationship("KnowledgeEntry", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name       = Column(String(255), nullable=False)
    # Roles: super_admin | store_admin | agent | customer
    role            = Column(String(50), default="customer")
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.datetime.utcnow)

    # NULL for super_admin; set for store_admin / agent
    tenant_id       = Column(String(36), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)

    tenant        = relationship("Tenant", foreign_keys=[tenant_id], back_populates="users")
    tickets       = relationship("Ticket", back_populates="assigned_agent", foreign_keys="[Ticket.assigned_agent_id]")
    conversations = relationship("Conversation", back_populates="customer")


class Conversation(Base):
    __tablename__ = "conversations"

    id         = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    tenant_id  = Column(String(36), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)
    customer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title      = Column(String(255), nullable=True)
    language   = Column(String(10), default="bn")
    sentiment  = Column(String(20), default="neutral")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    tenant    = relationship("Tenant",   back_populates="conversations")
    customer  = relationship("User",     back_populates="conversations")
    messages  = relationship("Message",  back_populates="conversation", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id               = Column(Integer, primary_key=True, index=True)
    conversation_id  = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    sender           = Column(String(50), nullable=False)   # user | bot | agent
    content          = Column(Text, nullable=False)
    confidence_score = Column(Float, default=1.0)
    sources          = Column(Text, nullable=True)
    timestamp        = Column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class Ticket(Base):
    __tablename__ = "tickets"

    id               = Column(Integer, primary_key=True, index=True)
    ticket_id        = Column(String(100), unique=True, index=True, nullable=False)
    tenant_id        = Column(String(36), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)
    customer_name    = Column(String(255), nullable=False)
    email            = Column(String(255), nullable=False)
    category         = Column(String(100), nullable=False)
    priority         = Column(String(50), default="medium")
    status           = Column(String(50), default="open")
    description      = Column(Text, nullable=False)
    sentiment        = Column(String(20), default="neutral")
    assigned_agent_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at       = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    tenant         = relationship("Tenant", back_populates="tickets")
    assigned_agent = relationship("User",   back_populates="tickets", foreign_keys=[assigned_agent_id])


class Feedback(Base):
    __tablename__ = "feedback"

    id              = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    rating          = Column(Integer, nullable=False)
    comment         = Column(Text, nullable=True)
    created_at      = Column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("Conversation", back_populates="feedbacks")


class Order(Base):
    __tablename__ = "orders"

    id                = Column(Integer, primary_key=True, index=True)
    order_id          = Column(String(50), unique=True, index=True, nullable=False)
    tenant_id         = Column(String(36), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)
    customer_name     = Column(String(255), nullable=False)
    customer_email    = Column(String(255), nullable=False)
    status            = Column(String(50), default="processing")
    items             = Column(Text, nullable=True)
    total_amount      = Column(Float, nullable=True)
    estimated_delivery = Column(String(100), nullable=True)
    created_at        = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at        = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class KnowledgeDocument(Base):
    """Uploaded file-based documents (super_admin managed)."""
    __tablename__ = "knowledge_documents"

    id         = Column(Integer, primary_key=True, index=True)
    filename   = Column(String(255), nullable=False)
    file_type  = Column(String(50), nullable=False)
    file_path  = Column(String(500), nullable=False)
    status     = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Product(Base):
    __tablename__ = "products"

    id          = Column(Integer, primary_key=True, index=True)
    tenant_id   = Column(String(36), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)
    name        = Column(String(255), nullable=False, index=True)
    name_bn     = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    price       = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)   # for showing discount
    category    = Column(String(100), nullable=True)
    features    = Column(Text, nullable=True)        # JSON array of feature strings
    in_stock    = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=datetime.datetime.utcnow)

    tenant = relationship("Tenant", foreign_keys=[tenant_id])


class KnowledgeEntry(Base):
    """Simple Q&A knowledge base entries managed directly by store admins."""
    __tablename__ = "knowledge_entries"

    id         = Column(Integer, primary_key=True, index=True)
    tenant_id  = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    question   = Column(Text, nullable=False)
    answer     = Column(Text, nullable=False)
    category   = Column(String(100), default="general")
    vector_id  = Column(String(36), nullable=True)  # ChromaDB doc ID (set after indexing)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    tenant = relationship("Tenant", back_populates="kb_entries")
