import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import uuid
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models import User, Order, Tenant
from app.auth import get_password_hash
from app.api.endpoints import api_router
from app.rag.vectorstore import vector_store

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 1. Initialize DB tables automatically on startup
logger.info("Initializing database schemas...")
Base.metadata.create_all(bind=engine)

def seed_database():
    """Seed base roles, tenants, and RAG documents so system works out of the box."""
    db = SessionLocal()
    try:
        # ── 1. Super Admin (platform owner) ──────────────────────────────────
        super_admin = db.query(User).filter(User.email == "super@platform.com").first()
        if not super_admin:
            super_admin = User(
                email="super@platform.com",
                hashed_password=get_password_hash("superpassword123"),
                full_name="Platform Super Admin",
                role="super_admin",
                is_active=True,
            )
            db.add(super_admin)
            logger.info("Super admin seeded: super@platform.com / superpassword123")

        # Legacy admin alias — keep existing integrations working
        legacy_admin = db.query(User).filter(User.email == "admin@example.com").first()
        if not legacy_admin:
            legacy_admin = User(
                email="admin@example.com",
                hashed_password=get_password_hash(settings.ADMIN_INITIAL_PASSWORD),
                full_name="System Administrator",
                role="super_admin",
                is_active=True,
            )
            db.add(legacy_admin)
            logger.info("Legacy admin seeded: admin@example.com / adminpassword123")

        db.commit()

        # ── 2. Demo Tenant: ShopBD ────────────────────────────────────────────
        shopbd = db.query(Tenant).filter(Tenant.name == "ShopBD").first()
        if not shopbd:
            shopbd = Tenant(
                id=str(uuid.uuid4()),
                name="ShopBD",
                domain="shopbd.com",
                api_key="sk_shopbd_demo_" + uuid.uuid4().hex[:12],
                plan="pro",
                widget_color="#6366f1",
                welcome_message="হ্যালো! ShopBD-তে স্বাগতম। কীভাবে সাহায্য করতে পারি?",
            )
            db.add(shopbd)
            db.commit()
            db.refresh(shopbd)
            logger.info(f"Demo tenant ShopBD created — API key: {shopbd.api_key}")

        # ShopBD store admin
        shopbd_admin = db.query(User).filter(User.email == "admin@shopbd.com").first()
        if not shopbd_admin:
            shopbd_admin = User(
                email="admin@shopbd.com",
                hashed_password=get_password_hash("storepassword123"),
                full_name="ShopBD Admin",
                role="store_admin",
                tenant_id=shopbd.id,
                is_active=True,
            )
            db.add(shopbd_admin)
            logger.info("ShopBD store admin seeded: admin@shopbd.com / storepassword123")

        # ShopBD support agent
        shopbd_agent = db.query(User).filter(User.email == "agent@shopbd.com").first()
        if not shopbd_agent:
            shopbd_agent = User(
                email="agent@shopbd.com",
                hashed_password=get_password_hash("agentpassword123"),
                full_name="Agent Rahat",
                role="agent",
                tenant_id=shopbd.id,
                is_active=True,
            )
            db.add(shopbd_agent)
            logger.info("ShopBD agent seeded: agent@shopbd.com / agentpassword123")

        # ── 3. Demo Tenant: FashionBD ─────────────────────────────────────────
        fashionbd = db.query(Tenant).filter(Tenant.name == "FashionBD").first()
        if not fashionbd:
            fashionbd = Tenant(
                id=str(uuid.uuid4()),
                name="FashionBD",
                domain="fashionbd.com.bd",
                api_key="sk_fashionbd_demo_" + uuid.uuid4().hex[:12],
                plan="free",
                widget_color="#ec4899",
                welcome_message="Hello! Welcome to FashionBD. How can I help you today?",
            )
            db.add(fashionbd)
            db.commit()
            db.refresh(fashionbd)
            logger.info(f"Demo tenant FashionBD created — API key: {fashionbd.api_key}")

        fashionbd_admin = db.query(User).filter(User.email == "admin@fashionbd.com").first()
        if not fashionbd_admin:
            fashionbd_admin = User(
                email="admin@fashionbd.com",
                hashed_password=get_password_hash("storepassword123"),
                full_name="FashionBD Admin",
                role="store_admin",
                tenant_id=fashionbd.id,
                is_active=True,
            )
            db.add(fashionbd_admin)
            logger.info("FashionBD store admin seeded: admin@fashionbd.com / storepassword123")

        # ── 4. Legacy agent/customer (backward compat) ────────────────────────
        legacy_agent = db.query(User).filter(User.email == "agent@example.com").first()
        if not legacy_agent:
            db.add(User(
                email="agent@example.com",
                hashed_password=get_password_hash("agentpassword123"),
                full_name="Agent Legacy",
                role="agent",
                tenant_id=shopbd.id,
                is_active=True,
            ))
        legacy_customer = db.query(User).filter(User.email == "customer@example.com").first()
        if not legacy_customer:
            db.add(User(
                email="customer@example.com",
                hashed_password=get_password_hash("customerpassword123"),
                full_name="Tahmid Hasan",
                role="customer",
                is_active=True,
            ))

        db.commit()
        logger.info("All users and tenants seeded successfully.")
    except Exception as e:
        logger.error(f"Error seeding user accounts: {e}")
        db.rollback()
    finally:
        db.close()

    # Seed sample orders so the chatbot can demonstrate real lookups
    db = SessionLocal()
    try:
        if db.query(Order).count() == 0:
            import json
            sample_orders = [
                Order(order_id="ORD-A1B2C", customer_name="Tahmid Hasan", customer_email="tahmid@example.com",
                      status="shipped", items=json.dumps(["Blue Panjabi", "Prayer Cap"]),
                      total_amount=1250.00, estimated_delivery="2026-06-22"),
                Order(order_id="ORD-D3E4F", customer_name="Nusrat Jahan", customer_email="nusrat@example.com",
                      status="processing", items=json.dumps(["Saree (Red)", "Blouse Piece"]),
                      total_amount=2800.00, estimated_delivery="2026-06-25"),
                Order(order_id="ORD-G5H6I", customer_name="Rahim Uddin", customer_email="rahim@example.com",
                      status="delivered", items=json.dumps(["Laptop Bag", "USB Hub"]),
                      total_amount=3500.00, estimated_delivery="2026-06-18"),
                Order(order_id="ORD-J7K8L", customer_name="Sumaiya Akter", customer_email="sumaiya@example.com",
                      status="out_for_delivery", items=json.dumps(["Kurta Set"]),
                      total_amount=950.00, estimated_delivery="2026-06-19"),
                Order(order_id="ORD-M9N0P", customer_name="Farhan Islam", customer_email="farhan@example.com",
                      status="cancelled", items=json.dumps(["Sneakers (Size 42)"]),
                      total_amount=4200.00, estimated_delivery=None),
            ]
            db.add_all(sample_orders)
            db.commit()
            logger.info("Sample orders seeded successfully.")
    except Exception as e:
        logger.error(f"Error seeding sample orders: {e}")
        db.rollback()
    finally:
        db.close()
        
    # Pre-seed Chroma vector database with sample customer support questions
    try:
        logger.info("Checking and seeding Chroma vector base FAQs...")
        sample_faqs = [
            "অর্ডার ডেলিভারিতে কত সময় লাগবে? সাধারণ ডেলিভারি সময় ঢাকা সিটির ভিতরে ২-৩ কার্যদিবস এবং ঢাকার বাইরে ৪-৫ কার্যদিবস।",
            "পেমেন্ট ফেরত পাওয়ার উপায় কী? যদি আপনি কোনো ত্রুটিযুক্ত পণ্য পেয়ে থাকেন, তবে ৩-৫ কার্যদিবসের মধ্যে আপনার মূল পেমেন্ট মাধ্যমে টাকা ফেরত দেওয়া হবে। অনুগ্রহ করে বিলিং পেজে সাপোর্ট টিকিট সাবমিট করুন।",
            "নতুন অর্ডারে কি কোনো ডিসকাউন্ট কুপন আছে? হ্যাঁ! আমাদের স্টোরে নতুন রেজিস্টার করলে প্রথম অর্ডারে ১০% ফ্ল্যাট ডিসকাউন্ট কুপন (কোড: WELCOME10) পাওয়া যাবে।",
            "রিফান্ড বা রিটার্ন পলিসি কী? পণ্য হাতে পাওয়ার ৭ দিনের মধ্যে অব্যবহৃত অবস্থায় মূল প্যাকেজিং সহ রিটার্ন বা রিফান্ড ক্লেইম করা যাবে।",
            "আপনাদের হেল্পলাইন বা কাস্টমার কেয়ার নাম্বার কত? আমাদের হটলাইন নাম্বার হলো ০৯৬১২৩৪৫৬৭৮ যা প্রতিদিন সকাল ৯টা থেকে রাত ৯টা পর্যন্ত সচল থাকে।"
        ]
        
        # Test if vector base is empty
        test_queries = vector_store.query_documents("ডেলিভারি", n_results=1)
        if not test_queries or test_queries[0]["confidence_score"] < 0.3:
            metas = [{"source": "sample_faq.txt", "type": "faq"} for _ in sample_faqs]
            vector_store.add_documents(sample_faqs, metas)
            logger.info("Chroma vector database FAQs successfully seeded.")
        else:
            logger.info("Vector database FAQ base already populated. Skipping seeding.")
    except Exception as e:
        logger.error(f"Error seeding vector database: {e}")

seed_database()

# 2. Instantiate FastAPI
app = FastAPI(
    title="Bangla AI Customer Support Platform",
    description="Enterprise RAG-enabled multilingual customer support chatbot and ticketing workspace.",
    version="1.0.0"
)

# 3. Configure CORS policies for UI communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend port/domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Bind routers
app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Bangla Customer Support API Backend",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
