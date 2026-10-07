# graph.py

from langgraph.graph import StateGraph, START, END

from state import AgentState

from nodes import (
    classify_request,
    answer_general,
    authenticate,
    company_lookup,
    answer_company,
    access_denied,
)


# ---------------------------------------------------------
# Routing functions
# ---------------------------------------------------------

def route_request(state: AgentState):
    if state.get("sensitive"):
        return "sensitive"

    return "general"


def route_authentication(state: AgentState):
    if state.get("authenticated") and state.get("authorized"):
        return "allowed"

    return "denied"


# ---------------------------------------------------------
# Create graph
# ---------------------------------------------------------

builder = StateGraph(AgentState)


# ---------------------------------------------------------
# Add nodes
# ---------------------------------------------------------

builder.add_node("classify", classify_request)

builder.add_node("general", answer_general)

builder.add_node("authenticate", authenticate)

builder.add_node("company_lookup", company_lookup)

builder.add_node("company_answer", answer_company)

builder.add_node("denied", access_denied)


# ---------------------------------------------------------
# Start of graph
# ---------------------------------------------------------

builder.add_edge(
    START   ,
    "classify"
)


# ---------------------------------------------------------
# Route after classification
# ---------------------------------------------------------

builder.add_conditional_edges(
    "classify",
    route_request,
    {
        "general": "general",
        "sensitive": "authenticate"
    }
)


# ---------------------------------------------------------
# Route after authentication
# ---------------------------------------------------------

builder.add_conditional_edges(
    "authenticate",
    route_authentication,
    {
        "allowed": "company_lookup",
        "denied": "denied"
    }
)


# ---------------------------------------------------------
# Normal edges
# ---------------------------------------------------------

builder.add_edge(
    "company_lookup",
    "company_answer"
)

builder.add_edge(
    "general",
    END
)

builder.add_edge(
    "company_answer",
    END
)

builder.add_edge(
    "denied",
    END
)


# ---------------------------------------------------------
# Compile graph
# ---------------------------------------------------------

graph = builder.compile()