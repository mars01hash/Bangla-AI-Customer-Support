from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langchain_core.messages import BaseMessage

def merge_messages(left: List[BaseMessage], right: List[BaseMessage]) -> List[BaseMessage]:
    """Reducer to append new messages to conversation state."""
    return left + right

class AgentState(TypedDict):
    # Core history
    messages: Annotated[List[BaseMessage], merge_messages]
    current_message: str
    
    # Metadata extracted by router/classifier
    detected_language: str       # 'bn', 'en', 'mixed'
    detected_sentiment: str      # 'positive', 'neutral', 'negative'
    category: str                # 'greeting', 'faq', 'billing', 'order', 'complaint', 'escalation'
    
    # RAG citations
    confidence_score: float
    sources: List[Dict[str, Any]]
    
    # Escalation states
    ticket_escalated: bool
    ticket_id: Optional[str]
    
    # Session identifiers
    session_id: str
    user_id: Optional[int]
    
    # Final output
    answer: str
