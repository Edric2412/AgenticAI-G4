import asyncio
import json
import httpx
from openai import AsyncOpenAI
from typing import Literal

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.state import DocumentState
from app.schemas import Scorecard, AuditCheck, TraceStep, get_default_checks
from app.config import settings

# ── Groq client — used by critic_node (Malikkarjun's implementation) ─
groq_client = AsyncOpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# ── Gemini REST endpoint — used by writer_node ────────────────────────
GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models"
    "/gemini-3.1-flash-lite:generateContent"
)

async def call_gemini(prompt: str) -> str:
    """
    Calls Gemini REST API asynchronously via httpx.
    Retries up to 3 times on 429 rate-limit errors.
    """
    api_key = settings.GEMINI_API_KEY

    if not api_key:
        return (
            "# Draft Document\n\n"
            "> ⚠️ **GEMINI_API_KEY not set.** Add your key to `.env`.\n\n"
            f"**Prompt sent:**\n```\n{prompt[:300]}...\n```"
        )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4096},
    }

    for attempt in range(3):
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                GEMINI_API_URL,
                params={"key": api_key},
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            if response.status_code == 429:
                await asyncio.sleep(40 * (attempt + 1))
                continue
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    raise Exception("Gemini API rate limit exceeded after 3 retries.")


# ── Prompt builders ───────────────────────────────────────────────────

def build_first_draft_prompt(archetype: str, payload_text: str, context: str) -> str:
    return f"""You are a professional document writing AI specialising in {archetype} documents.

COMPLIANCE & STYLE CONTEXT:
{context}

DOCUMENT ARCHETYPE: {archetype}

USER BRIEF:
{payload_text}

INSTRUCTIONS:
- Output ONLY the Markdown document. No preamble, no commentary.
- Use ## headings, ### sub-headings, tables, blockquotes for important notes.
- Be specific and detailed — the document should be immediately usable.
- Include: executive summary, functional requirements, technical constraints, compliance checklist.
"""


def build_revision_prompt(
    archetype: str, existing_document: str, feedback: str, context: str
) -> str:
    return f"""You are a professional document revision AI specialising in {archetype} documents.

Revise the document below based on the feedback. Only change what the feedback asks for.
Output ONLY the complete revised Markdown document. No preamble or commentary.

COMPLIANCE & STYLE CONTEXT:
{context}

CURRENT DOCUMENT DRAFT:
{existing_document}

HUMAN REVIEWER FEEDBACK:
{feedback}

Output the full revised document below:
"""


# ── WRITER NODE ───────────────────────────────────────────────────────

async def writer_node(state: DocumentState) -> dict:
    """
    Writer Agent: Uses Gemini to draft or revise the Markdown document.

    TWO MODES:
      - First draft (loopCount == 0): generates from payloadText + pgvector context.
      - Revision (feedback present): revises existing doc based on feedback.

    CHECKPOINTER NOTE:
      Returns feedback=None so MemorySaver checkpoints the cleared value,
      preventing the same feedback from re-triggering on the next loop.
    """
    loop_count = state.get("loopCount", 0)
    archetype = state.get("archetype", "Technical")
    payload = state.get("payloadText", "")
    feedback = state.get("feedback")

    # Retrieve pgvector context if semanticEnrichment is enabled
    context = ""
    if state.get("semanticEnrichment", True):
        try:
            from app.db import retrieve_context
            context = await retrieve_context(query=payload, archetype=archetype)
        except Exception:
            context = "No style guide context available (DB not connected)."

    # Build prompt based on mode
    if feedback:
        existing_doc = state.get("documentContent", "")
        prompt = build_revision_prompt(archetype, existing_doc, feedback, context)
        trace_description = f"Document revised based on feedback (Cycle {loop_count})."
    else:
        prompt = build_first_draft_prompt(archetype, payload, context)
        trace_description = "Initial document draft synthesized by Gemini."

    # Call Gemini
    try:
        document_content = await call_gemini(prompt)
    except httpx.HTTPStatusError as e:
        document_content = (
            f"# ⚠️ Gemini API Error\n\n"
            f"**Status:** {e.response.status_code}\n\n"
            f"**Detail:** {e.response.text}\n\n"
            f"Check `GEMINI_API_KEY` in `.env` and verify the model name."
        )
    except Exception as e:
        document_content = (
            f"# ⚠️ Unexpected Error in Writer Node\n\n```\n{str(e)}\n```"
        )

    # Update trace steps
    trace = list(state.get("trace", []))
    if loop_count == 0:
        trace[0] = TraceStep(id="1", name="Context Analysis",
                             description="Payload and pgvector context analysed.",
                             status="completed")
        trace[1] = TraceStep(id="2", name="Architecture Mapping",
                             description="Document archetype and structure mapped.",
                             status="completed")
        trace[2] = TraceStep(id="3", name="PRD Synthesis",
                             description=trace_description,
                             status="completed", progress=100)
    else:
        trace[2] = TraceStep(id="3", name="PRD Synthesis",
                             description=trace_description,
                             status="completed", progress=100)

    return {
        **state,
        "documentContent": document_content,
        "feedback": None,       # ← clears feedback from checkpoint
        "trace": trace,
        "status": "running",
    }


# ── CRITIC NODE (Malikkarjun's Groq implementation — merged) ─────────

async def critic_node(state: DocumentState) -> dict:
    """
    Critic Agent: Evaluates the draft using Groq Llama 3.3 70B.
    Returns a structured Scorecard.
    """
    document = state.get("documentContent", "")
    archetype = state.get("archetype", "Technical")
    conflict_detect = state.get("conflictDetection", False)

    # Get dynamic check structures based on the document archetype
    default_checks = get_default_checks(archetype, conflict_detect)
    checks_eval_str = "\n    ".join([f"{idx+1}. {c['name']}" for idx, c in enumerate(default_checks)])
    schema_checks_json = json.dumps([
        {"id": c["id"], "name": c["name"], "status": "verified|attention|pending"}
        for c in default_checks
    ], indent=4)

    conflict_instr = ""
    if conflict_detect:
        conflict_instr = (
            f"\n    {len(default_checks)+3}. Contradiction & Conflict Detection:\n"
            "    Verify that the document contains no internal contradictions, conflicts, or inconsistent "
            "statements across sections. If any contradictions exist, mark status as 'attention' and "
            "list them in the summary."
        )

    prompt = f"""
    You are a senior enterprise compliance reviewer specializing in {archetype} auditing.

    Review the following professional document.

    Evaluate:
    {checks_eval_str}
    {len(default_checks)+1}. Structural Completeness
    {len(default_checks)+2}. Compliance Quality{conflict_instr}

    Return STRICT JSON ONLY.

    Required JSON Schema:
{{
  "score": integer,
  "checks": {schema_checks_json},
  "summary": "short critique summary"
}}

    Document:
    {document}
    """

    try:
        response = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        cleaned = content.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(cleaned)
        scorecard = Scorecard(**parsed)

    except Exception as e:
        raise RuntimeError(f"Groq critique generation failed: {str(e)}")

    trace = list(state.get("trace", []))
    trace[3] = TraceStep(
        id="4", name="Validation Check",
        description="Audit checks completed by Critic.",
        status="completed"
    )

    return {**state, "scorecard": scorecard, "trace": trace}


# ── HUMAN ARBITRATION NODE ────────────────────────────────────────────

async def human_arbitration_node(state: DocumentState) -> dict:
    """
    Interrupt gate.

    IMPORTANT: Due to interrupt_before=["human_arbitration_node"], this node
    only actually EXECUTES when the graph is RESUMED (after user submits
    feedback or approves). When the graph first pauses here, the node does
    NOT run — LangGraph freezes before it.

    FIX (Issue 2): Do NOT set status="paused" here. Setting paused here
    would overwrite the "running" status injected by feedback/approve,
    breaking the transition. Status management is handled by main.py and
    the SSE generator instead.

    The conditional edge after this node (route_after_arbitration) handles
    routing to writer_node or deployment_node based on what the user did.
    """
    return {**state}


async def deployment_node(state: DocumentState) -> dict:
    """Final node — marks document as completed."""
    return {**state, "status": "completed"}


# ── ROUTER: critic → next node ────────────────────────────────────────

def route_evaluation(
    state: DocumentState,
) -> Literal["writer_node", "human_arbitration_node", "deployment_node"]:
    score = state["scorecard"].score
    loop_count = state.get("loopCount", 0)
    max_loops = state.get("maxLoops", 3)

    if score >= 95:
        return "deployment_node"
    if loop_count >= max_loops:
        return "human_arbitration_node"
    if state.get("feedback") is not None:
        return "writer_node"
    return "human_arbitration_node"


# ── ROUTER: after human_arbitration_node ─────────────────────────────

def route_after_arbitration(
    state: DocumentState,
) -> Literal["writer_node", "deployment_node"]:
    """
    FIX (Issue 3): Replaces the static edge human_arbitration_node → END.

    When the graph resumes after a human pause, this router decides:
    - Score >= 95 (forced by approve endpoint) → deployment_node
    - Feedback present → writer_node for revision
    - Default fallback → deployment_node
    """
    scorecard = state.get("scorecard")
    score = scorecard.score if hasattr(scorecard, "score") else 0

    if score >= 95:
        return "deployment_node"
    if state.get("feedback") is not None:
        return "writer_node"
    return "deployment_node"


# ── GRAPH ASSEMBLY ────────────────────────────────────────────────────

workflow = StateGraph(DocumentState)

workflow.add_node("writer_node",            writer_node)
workflow.add_node("critic_node",            critic_node)
workflow.add_node("human_arbitration_node", human_arbitration_node)
workflow.add_node("deployment_node",        deployment_node)

workflow.add_edge(START, "writer_node")
workflow.add_edge("writer_node", "critic_node")

workflow.add_conditional_edges(
    "critic_node",
    route_evaluation,
    {
        "writer_node":            "writer_node",
        "human_arbitration_node": "human_arbitration_node",
        "deployment_node":        "deployment_node",
    },
)

# FIX (Issue 3): Replace static edge to END with conditional routing.
# Previously: workflow.add_edge("human_arbitration_node", END)
# This caused writer revision loop and deployment node to be unreachable.
workflow.add_conditional_edges(
    "human_arbitration_node",
    route_after_arbitration,
    {
        "writer_node":    "writer_node",
        "deployment_node": "deployment_node",
    },
)

workflow.add_edge("deployment_node", END)

# ── MEMORY CHECKPOINTER ───────────────────────────────────────────────
# MemorySaver stores state snapshots in RAM.
# For production: swap with AsyncPostgresSaver once DB is ready.
memory = MemorySaver()

app_graph = workflow.compile(
    checkpointer=memory,
    interrupt_before=["human_arbitration_node"],  # ← HITL pause point
)