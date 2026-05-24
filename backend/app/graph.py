from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.state import DocumentState
from app.schemas import Scorecard, AuditCheck, TraceStep

# =====================================================================
# TASK ASSIGNMENT: TEAMMATE B (Intermediate/Strong Teammate)
# TODO: Implement actual LLM API calls in writer_node and critic_node
# =====================================================================

async def writer_node(state: DocumentState) -> DocumentState:
    """
    Writer Agent: Ingests payload & retrievals to compile/revise markdown.
    
    ASSIGNMENT (Teammate B):
    - Connect to gemini-3.1-flash-lite.
    - Feed in raw payload and context retrieved from pgvector.
    - If state['feedback'] exists, perform localized revision.
    """
    loop_count = state.get("loopCount", 0)
    archetype = state.get("archetype", "Technical")
    
    # Simple simulated drafting
    if loop_count == 0:
        content = f"# Product Requirements: DocuFlow AI Core ({archetype})\n\n"
        content += "This document outlines the core agentic capabilities for the next-generation document orchestration platform.\n\n"
        content += "### 1. Functional Objectives\n"
        content += "* Automated discovery of document relationships across 256+ data types.\n"
        content += "* Integration with 'Aurora' state management for visual processing feedback.\n"
        content += "* Multi-agent negotiation for conflicting compliance requirements.\n\n"
        content += "> **AGENT NOTE**\n"
        content += "> The 'Compliance Check' module has been expanded to include Data Sovereignty protocols.\n\n"
        content += "### 2. Technical Constraints\n"
        content += "| Attribute | Spec |\n| --- | --- |\n| Latency Target | < 150ms |\n| Uptime SLA | 99.99% |\n"
    else:
        # Append revision if user sent feedback
        feedback = state.get("feedback", "No feedback provided.")
        content = state.get("documentContent", "")
        content += f"\n### 3. Revision (Cycle {loop_count})\n"
        content += f"* Amended text based on user feedback: *\"{feedback}\"*\n"
        content += "* Token bucket algorithms implemented natively at gateway level.\n"
        content += "* Support for backpressure indicators on active WS channels.\n"
        content += "* Dynamic queuing for request throttling up to 10k concurrent sessions.\n"

    # Update state
    trace = list(state.get("trace", []))
    if loop_count == 0:
        trace[0] = TraceStep(id="1", name="Context Analysis", description="Completed context analysis.", status="completed")
        trace[1] = TraceStep(id="2", name="Architecture Mapping", description="Completed architecture mapping.", status="completed")
        trace[2] = TraceStep(id="3", name="PRD Synthesis", description="Document draft synthesized.", status="completed", progress=100)
    else:
        trace[2] = TraceStep(id="3", name="PRD Synthesis", description=f"Document revised (Cycle {loop_count}).", status="completed", progress=100)
        
    return {
        **state,
        "documentContent": content,
        "trace": trace,
        "status": "running"
    }

async def critic_node(state: DocumentState) -> DocumentState:
    """
    Critic Agent: Evaluates the draft and outputs a structured Pydantic scorecard.
    
    ASSIGNMENT (Teammate B):
    - Connect to Groq (Llama 3.3 70B).
    - Request JSON matching schemas.Scorecard schema.
    - Check compliance metrics, code styles, and data safety bounds.
    """
    loop_count = state.get("loopCount", 0)
    
    # Simulated scorecard output
    if loop_count == 0:
        scorecard = Scorecard(
            score=88,
            checks=[
                AuditCheck(id="sec", name="Security Layer", status="verified"),
                AuditCheck(id="sov", name="Data Sovereignty", status="verified"),
                AuditCheck(id="tok", name="Token Handling", status="attention"),
                AuditCheck(id="rat", name="Rate Limiting", status="pending")
            ],
            summary="Critic flagged missing Rate Limiting specs and ambiguous Token Handling protocols."
        )
    else:
        scorecard = Scorecard(
            score=98,
            checks=[
                AuditCheck(id="sec", name="Security Layer", status="verified"),
                AuditCheck(id="sov", name="Data Sovereignty", status="verified"),
                AuditCheck(id="tok", name="Token Handling", status="verified"),
                AuditCheck(id="rat", name="Rate Limiting", status="verified")
            ],
            summary="Critic check verified. Rate Limiting and Token Handling meet design requirements."
        )

    trace = list(state.get("trace", []))
    trace[3] = TraceStep(id="4", name="Validation Check", description="Audit checks completed.", status="completed")
    
    return {
        **state,
        "scorecard": scorecard,
        "trace": trace
    }

async def human_arbitration_node(state: DocumentState) -> DocumentState:
    """
    Interrupt gate node. Transition status to 'paused' and wait for user resume inputs.
    """
    return {
        **state,
        "status": "paused"
    }

async def deployment_node(state: DocumentState) -> DocumentState:
    """
    Finalize approval, set status to 'completed'.
    """
    return {
        **state,
        "status": "completed"
    }

# Router logic
def route_evaluation(state: DocumentState) -> Literal["writer_node", "human_arbitration_node", "deployment_node"]:
    score = state["scorecard"]["score"]
    loop_count = state.get("loopCount", 0)
    max_loops = state.get("maxLoops", 3)
    
    # 1. If score is passing, proceed to deployment node
    if score >= 95:
        return "deployment_node"
        
    # 2. Circuit Breaker: If max cycles exceeded, route to HITL human_arbitration
    if loop_count >= max_loops:
        return "human_arbitration_node"
        
    # 3. If there is new user feedback that hasn't been applied yet, route back to writer
    # (The API will set 'feedback' and resume the graph)
    if state.get("feedback") is not None:
        return "writer_node"
        
    # 4. Otherwise, pause and wait for user interaction
    return "human_arbitration_node"


# --- Graph Assembly ---

workflow = StateGraph(DocumentState)

# Add Node Definitions
workflow.add_node("writer_node", writer_node)
workflow.add_node("critic_node", critic_node)
workflow.add_node("human_arbitration_node", human_arbitration_node)
workflow.add_node("deployment_node", deployment_node)

# Set Entrypoint
workflow.add_edge(START, "writer_node")

# Flow paths
workflow.add_edge("writer_node", "critic_node")

# Conditional Router Edge (from Critic output)
workflow.add_conditional_edges(
    "critic_node",
    route_evaluation,
    {
        "writer_node": "writer_node",
        "human_arbitration_node": "human_arbitration_node",
        "deployment_node": "deployment_node"
    }
)

# Terminals
workflow.add_edge("human_arbitration_node", END)
workflow.add_edge("deployment_node", END)

# Persistent Memory Saver (in-memory checkpointing for local development/stubs)
memory = MemorySaver()

# Compile the DAG graph with an interrupt before the human gatekeeper node
# This freezes the LangGraph thread state for FastAPI REST resumption
app_graph = workflow.compile(
    checkpointer=memory,
    interrupt_before=["human_arbitration_node"]
)
