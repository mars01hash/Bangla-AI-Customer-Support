import logging
from langgraph.graph import StateGraph, END, START
from app.agents.state import AgentState
from app.agents.nodes import (
    language_sentiment_detector_node,
    greeting_agent_node,
    faq_agent_node,
    order_support_agent_node,
    billing_agent_node,
    complaint_agent_node,
    escalation_agent_node,
    product_agent_node,
    order_placement_agent_node,
)

logger = logging.getLogger(__name__)

# --- Routers ---

def route_from_detector(state: AgentState) -> str:
    """Route message to appropriate agent based on detected intent category."""
    category = state.get("category", "faq")
    logger.info(f"Routing edge from detector: category is '{category}'")

    if category in ["greeting", "faq", "order", "billing", "complaint", "escalation", "product", "order_placement"]:
        return category
    return "faq"

def route_from_faq(state: AgentState) -> str:
    """Reroute to escalation if RAG confidence score was below threshold."""
    category = state.get("category", "faq")
    if category == "escalation":
        logger.info("Routing FAQ node -> Escalation node (low confidence)")
        return "escalation"
    return END

def route_from_complaint(state: AgentState) -> str:
    """Reroute to escalation if complaint sentiment was negative."""
    category = state.get("category", "complaint")
    if category == "escalation":
        logger.info("Routing Complaint node -> Escalation node (negative sentiment)")
        return "escalation"
    return END


# --- Graph Construction ---

# 1. Initialize StateGraph
builder = StateGraph(AgentState)

# 2. Add Nodes
builder.add_node("detector", language_sentiment_detector_node)
builder.add_node("greeting", greeting_agent_node)
builder.add_node("faq", faq_agent_node)
builder.add_node("order", order_support_agent_node)
builder.add_node("billing", billing_agent_node)
builder.add_node("complaint", complaint_agent_node)
builder.add_node("escalation", escalation_agent_node)
builder.add_node("product", product_agent_node)
builder.add_node("order_placement", order_placement_agent_node)

# 3. Define Entry Point
builder.add_edge(START, "detector")

# 4. Add Routing Edges
builder.add_conditional_edges(
    "detector",
    route_from_detector,
    {
        "greeting": "greeting",
        "faq": "faq",
        "order": "order",
        "billing": "billing",
        "complaint": "complaint",
        "escalation": "escalation",
        "product": "product",
        "order_placement": "order_placement",
    }
)

builder.add_conditional_edges(
    "faq",
    route_from_faq,
    {
        "escalation": "escalation",
        END: END
    }
)

builder.add_conditional_edges(
    "complaint",
    route_from_complaint,
    {
        "escalation": "escalation",
        END: END
    }
)

# 5. Define End Edges for terminal nodes
builder.add_edge("greeting", END)
builder.add_edge("order", END)
builder.add_edge("billing", END)
builder.add_edge("escalation", END)
builder.add_edge("product", END)
builder.add_edge("order_placement", END)

# 6. Compile Graph
support_graph = builder.compile()
logger.info("LangGraph Customer Support Workflow compiled successfully.")
