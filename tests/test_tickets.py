import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Ticket

# Set up in-memory SQLite database for test runtime isolation
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # Create all tables in-memory
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test completes
        Base.metadata.drop_all(bind=engine)

def test_ticket_creation_and_modification(db_session):
    # Register test ticket
    new_ticket = Ticket(
        ticket_id="TKT-TEST101",
        customer_name="Test Customer",
        email="test@example.com",
        category="technical",
        priority="medium",
        status="open",
        description="Unable to access payment portal.",
        sentiment="neutral"
    )
    db_session.add(new_ticket)
    db_session.commit()
    
    # Query ticket
    retrieved = db_session.query(Ticket).filter(Ticket.ticket_id == "TKT-TEST101").first()
    assert retrieved is not None
    assert retrieved.customer_name == "Test Customer"
    assert retrieved.status == "open"
    
    # Modify status and priority
    retrieved.status = "in_progress"
    retrieved.priority = "high"
    db_session.commit()
    
    # Re-fetch and verify changes
    updated = db_session.query(Ticket).filter(Ticket.ticket_id == "TKT-TEST101").first()
    assert updated.status == "in_progress"
    assert updated.priority == "high"
