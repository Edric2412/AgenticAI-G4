import asyncio
import json
import httpx
from typing import Literal

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.state import DocumentState
from app.schemas import Scorecard, AuditCheck, TraceStep
from app.config import settings

# =====================================================================
# GEMINI API HELPER
# Uses httpx (already in requirements) to call Gemini REST API async.
# No extra package needed — httpx is already listed.
# =====================================================================

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models"
    "/gemini-3.1-flash-lite:generateContent"
)

async def call_gemini(prompt: str) -> str:
    api_key = settings.GEMINI_API_KEY

    if not api_key:
        return (
            "# Draft Document\n\n"
            "> ⚠️ **GEMINI_API_KEY not set.** "
            "This is a placeholder. Add your key to the `.env` file.\n\n"
            f"**Prompt sent to model:**\n```\n{prompt[:300]}...\n```"
        )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048,
        }
    }

    for attempt in range(3):
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                GEMINI_API_URL,
                params={"key": api_key},
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 429:
                wait = 40 * (attempt + 1)
                await asyncio.sleep(wait)
                continue
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    raise Exception("Gemini API rate limit exceeded after 3 retries.")


# =====================================================================
# PROMPT BUILDERS
# Separated from the node logic so they are easy to tune later.
# =====================================================================

def build_first_draft_prompt(archetype: str, payload_text: str, context: str) -> str:
    """Prompt for generating a brand-new document from scratch."""
    return f"""You are a professional document writing AI specialising in {archetype} documents.

Below is a compliance and style context retrieved from the knowledge base, followed by the user's brief.
Your job is to produce a complete, well-structured Markdown document that satisfies the brief and follows the style rules.

---
COMPLIANCE & STYLE CONTEXT:
{context}

---
DOCUMENT ARCHETYPE: {archetype}

USER BRIEF:
{payload_text}

---
INSTRUCTIONS:
- Output ONLY the Markdown document. No preamble, no explanation, no commentary.
- Use proper Markdown: ## headings, ### sub-headings, tables, blockquotes for important notes, bold for key terms.
- Be specific and detailed — the document should be immediately usable.
- Include at least: an executive summary, functional requirements, technical constraints, and a compliance checklist.
"""


def build_revision_prompt(
    archetype: str,
    existing_document: str,
    feedback: str,
    context: str
) -> str:
    """Prompt for revising an existing document based on user feedback."""
    return f"""You are a professional document revision AI specialising in {archetype} documents.

Below is the current draft of the document and specific feedback from a human reviewer.
Revise the document to address the feedback precisely.

RULES:
- Preserve all sections that the feedback does NOT mention.
- Only change what the feedback explicitly asks to fix or improve.
- Output ONLY the complete revised Markdown document. No preamble, no commentary.

---
COMPLIANCE & STYLE CONTEXT:
{context}

---
CURRENT DOCUMENT DRAFT:
{existing_document}

---
HUMAN REVIEWER FEEDBACK:
{feedback}

---
Output the full revised document below:
"""


# =====================================================================
# WRITER NODE  ← YOUR PRIMARY TASK
# =====================================================================

async def writer_node(state: DocumentState) -> dict:
    """
    Writer Agent: Uses Gemini gemini-2.0-flash-lite to draft or revise
    the Markdown document stored in state['documentContent'].

    TWO MODES:
      1. First draft  (loopCount == 0, no feedback):
         Builds a fresh document from payloadText + pgvector context.

      2. Revision     (feedback is present):
         Sends the existing draft + feedback to Gemini for targeted revision.
         Clears feedback from state after applying it so it doesn't re-trigger.

    CHECKPOINTER NOTE:
      LangGraph's MemorySaver snapshots the entire state dict after this node
      returns. That means the cleared feedback (`"feedback": None`) is
      persisted in the checkpoint — the graph will NOT re-apply the same
      feedback on a future resume. This is the key mechanism for safe looping.
    """
    loop_count = state.get("loopCount", 0)
    archetype  = state.get("archetype", "Technical")
    payload    = state.get("payloadText", "")
    feedback   = state.get("feedback")           # None on first run

    # --- Retrieve style/compliance context from pgvector (Teammate C's function) ---
    # This is already a stub that returns safe placeholder text, so calling it
    # here is safe even before Teammate C implements the real embedding lookup.
    from app.db import retrieve_context
    context = await retrieve_context(query=payload, archetype=archetype)

    # --- Build the right prompt based on mode ---
    if feedback:
        # REVISION MODE — user submitted feedback, apply it
        existing_doc = state.get("documentContent", "")
        prompt = build_revision_prompt(archetype, existing_doc, feedback, context)
        trace_description = f"Document revised based on feedback (Cycle {loop_count})."
    else:
        # FIRST DRAFT MODE — generate from scratch
        prompt = build_first_draft_prompt(archetype, payload, context)
        trace_description = "Initial document draft synthesized by Gemini."

    # --- Call Gemini ---
    try:
        document_content = await call_gemini(prompt)
    except httpx.HTTPStatusError as e:
        # Surface API errors clearly in the document so the team can debug
        document_content = (
            f"# ⚠️ Gemini API Error\n\n"
            f"**Status:** {e.response.status_code}\n\n"
            f"**Detail:** {e.response.text}\n\n"
            f"Check that `GEMINI_API_KEY` in `.env` is valid and the model name is correct."
        )
    except Exception as e:
        document_content = (
            f"# ⚠️ Unexpected Error in Writer Node\n\n```\n{str(e)}\n```"
        )

    # --- Update trace steps ---
    trace = list(state.get("trace", []))
    if loop_count == 0:
        # Mark the first three trace steps complete on the initial draft
        trace[0] = TraceStep(
            id="1", name="Context Analysis",
            description="Payload and pgvector context analysed.",
            status="completed"
        )
        trace[1] = TraceStep(
            id="2", name="Architecture Mapping",
            description="Document archetype and structure mapped.",
            status="completed"
        )
        trace[2] = TraceStep(
            id="3", name="PRD Synthesis",
            description=trace_description,
            status="completed", progress=100
        )
    else:
        # On revisions, only update the synthesis step
        trace[2] = TraceStep(
            id="3", name="PRD Synthesis",
            description=trace_description,
            status="completed", progress=100
        )

    # --- Return updated state ---
    # IMPORTANT: Set feedback=None after applying it.
    # MemorySaver will checkpoint this None, preventing the same feedback
    # from being re-applied if the graph loops back through writer_node again.
    return {
        **state,
        "documentContent": document_content,
        "feedback": None,           # ← clears feedback from checkpoint
        "trace": trace,
        "status": "running",
    }


# =====================================================================
# CRITIC NODE  (stub — Teammate B's second task or team lead's task)
# Left as-is. The simulated scorecard drives the router correctly.
# Replace the internals with real Groq API calls when ready.
# =====================================================================

async def critic_node(state: DocumentState) -> dict:
    """
    Critic Agent: Evaluates the draft and outputs a structured scorecard.
    Currently simulated. Replace with Groq Llama 3.3 70B call when assigned.
    """
    loop_count = state.get("loopCount", 0)

    if loop_count == 0:
        scorecard = Scorecard(
            score=88,
            checks=[
                AuditCheck(id="sec", name="Security Layer",    status="verified"),
                AuditCheck(id="sov", name="Data Sovereignty",  status="verified"),
                AuditCheck(id="tok", name="Token Handling",    status="attention"),
                AuditCheck(id="rat", name="Rate Limiting",     status="pending"),
            ],
            summary=(
                "Critic flagged missing Rate Limiting specs "
                "and ambiguous Token Handling protocols."
            )
        )
    else:
        scorecard = Scorecard(
            score=98,
            checks=[
                AuditCheck(id="sec", name="Security Layer",    status="verified"),
                AuditCheck(id="sov", name="Data Sovereignty",  status="verified"),
                AuditCheck(id="tok", name="Token Handling",    status="verified"),
                AuditCheck(id="rat", name="Rate Limiting",     status="verified"),
            ],
            summary=(
                "All checks verified. Rate Limiting and Token Handling "
                "meet design requirements."
            )
        )

    trace = list(state.get("trace", []))
    trace[3] = TraceStep(
        id="4", name="Validation Check",
        description="Audit checks completed by Critic.",
        status="completed"
    )

    return {
        **state,
        "scorecard": scorecard,
        "trace": trace,
    }


# =====================================================================
# HUMAN ARBITRATION NODE
# Pauses the graph. MemorySaver freezes state here.
# FastAPI's /feedback and /approve endpoints inject new values and resume.
# =====================================================================

async def human_arbitration_node(state: DocumentState) -> dict:
    """
    Interrupt gate. Sets status='paused'.
    LangGraph stops execution here (interrupt_before) and the MemorySaver
    checkpoints the frozen state so FastAPI can read and update it via REST.
    """
    return {
        **state,
        "status": "paused",
    }


async def deployment_node(state: DocumentState) -> dict:
    """Final node. Marks the document as completed."""
    return {
        **state,
        "status": "completed",
    }


# =====================================================================
# ROUTER LOGIC
# Reads the scorecard score and loopCount from state to decide next node.
# =====================================================================

def route_evaluation(
    state: DocumentState,
) -> Literal["writer_node", "human_arbitration_node", "deployment_node"]:
    scorecard = state["scorecard"]
    score = scorecard.score if hasattr(scorecard, "score") else scorecard["score"]
    loop_count = state.get("loopCount", 0)
    max_loops  = state.get("maxLoops", 3)

    # Score is high enough → ship it
    if score >= 95:
        return "deployment_node"

    # Circuit breaker: too many auto-loops → hand off to human
    if loop_count >= max_loops:
        return "human_arbitration_node"

    # Feedback was injected by the user and already cleared in writer_node,
    # but if for some reason it's still set here, route back to writer
    if state.get("feedback") is not None:
        return "writer_node"

    # Score too low but no feedback yet → pause and wait for human input
    return "human_arbitration_node"


# =====================================================================
# GRAPH ASSEMBLY  (unchanged from original — do not modify)
# =====================================================================

workflow = StateGraph(DocumentState)

workflow.add_node("writer_node",           writer_node)
workflow.add_node("critic_node",           critic_node)
workflow.add_node("human_arbitration_node", human_arbitration_node)
workflow.add_node("deployment_node",       deployment_node)

workflow.add_edge(START, "writer_node")
workflow.add_edge("writer_node", "critic_node")

workflow.add_conditional_edges(
    "critic_node",
    route_evaluation,
    {
        "writer_node":            "writer_node",
        "human_arbitration_node": "human_arbitration_node",
        "deployment_node":        "deployment_node",
    }
)

workflow.add_edge("human_arbitration_node", END)
workflow.add_edge("deployment_node",        END)

# =====================================================================
# MEMORY CHECKPOINTER
#
# MemorySaver stores every state snapshot in-process (RAM).
# This means the graph can be paused at human_arbitration_node and
# resumed later via FastAPI — state is not lost between HTTP requests.
#
# For production: swap MemorySaver for SqliteSaver or AsyncPostgresSaver
# once Teammate A's DB models are ready, like this:
#
#   from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
#   memory = AsyncSqliteSaver.from_conn_string("sqlite+aiosqlite:///./docuflow.db")
#
# The rest of the graph code stays identical — the checkpointer is
# pluggable without any node changes.
# =====================================================================

memory = MemorySaver()

app_graph = workflow.compile(
    checkpointer=memory,
    interrupt_before=["human_arbitration_node"],   # ← pause point for HITL
)