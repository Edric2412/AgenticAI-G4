import asyncio
import json
import uuid
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from app.schemas import (
    CreateDocumentRequest,
    FeedbackRequest,
    DocumentSessionResponse,
    Scorecard,
    AuditCheck,
    TraceStep
)
from app.graph import app_graph
from app.state import DocumentState

app = FastAPI(title="DocuFlow AI Backend Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_configs = {}

# ── Helper: serialize Pydantic objects to JSON ────────────────────────
def to_json(obj) -> str:
    return json.dumps(
        obj,
        default=lambda o: o.model_dump() if hasattr(o, "model_dump") else str(o)
    )


@app.post("/api/documents", status_code=201)
async def create_document(request: CreateDocumentRequest):
    session_id = f"dfl_{uuid.uuid4().hex[:9]}"

    session_configs[session_id] = {
        "maxLoops": request.loopGuard,
        "archetype": request.archetype,
        "payloadText": request.payloadText
    }

    initial_state: DocumentState = {
        "sessionId": session_id,
        "archetype": request.archetype,
        "documentContent": "",
        "status": "running",
        "loopCount": 0,
        "maxLoops": request.loopGuard,
        "scorecard": Scorecard(
            score=0,
            checks=[
                AuditCheck(id="sec", name="Security Layer",   status="pending"),
                AuditCheck(id="sov", name="Data Sovereignty", status="pending"),
                AuditCheck(id="tok", name="Token Handling",   status="pending"),
                AuditCheck(id="rat", name="Rate Limiting",    status="pending"),
            ],
            summary="Awaiting analysis initialization."
        ),
        "trace": [
            TraceStep(id="1", name="Context Analysis",    description="Analyzing inputs...",             status="pending"),
            TraceStep(id="2", name="Architecture Mapping",description="Mapping nodes...",                status="pending"),
            TraceStep(id="3", name="PRD Synthesis",       description="Preparing drafting compiler...", status="pending"),
            TraceStep(id="4", name="Validation Check",    description="Awaiting draft...",              status="pending"),
        ],
        "payloadText": request.payloadText,
        "feedback": None,
        "current_step": "init"
    }

    config = {"configurable": {"thread_id": session_id}}
    await app_graph.ainvoke(initial_state, config=config)

    # LangGraph stops BEFORE human_arbitration_node due to interrupt_before.
    # That node never runs, so status stays "running" in the checkpoint.
    # We manually set it to "paused" so the frontend knows to stop and
    # enable the Approve & Request Revision buttons.
    state_info = await app_graph.aget_state(config)
    if state_info and state_info.next and "human_arbitration_node" in state_info.next:
        await app_graph.aupdate_state(config, {"status": "paused"})

    return {"sessionId": session_id}


@app.api_route("/api/documents/{sessionId}", methods=["GET", "HEAD"])
async def get_document_state(sessionId: str, request: Request):
    if request.method == "HEAD":
        return Response(status_code=200)

    config = {"configurable": {"thread_id": sessionId}}
    state_info = await app_graph.aget_state(config)

    if not state_info or not state_info.values:
        raise HTTPException(status_code=404, detail="Document session not found.")

    return json.loads(to_json(state_info.values))


@app.post("/api/documents/{sessionId}/feedback")
async def submit_revision_feedback(sessionId: str, request: FeedbackRequest):
    config = {"configurable": {"thread_id": sessionId}}
    state_info = await app_graph.aget_state(config)

    if not state_info or not state_info.values:
        raise HTTPException(status_code=404, detail="Session thread not found.")

    current_loops = state_info.values.get("loopCount", 0)

    await app_graph.aupdate_state(config, {
        "feedback": request.feedback,
        "loopCount": current_loops + 1,
        "status": "running"
    })

    await app_graph.ainvoke(None, config=config)

    # Same interrupt fix — set paused if graph stopped at HITL node
    state_info = await app_graph.aget_state(config)
    if state_info and state_info.next and "human_arbitration_node" in state_info.next:
        await app_graph.aupdate_state(config, {"status": "paused"})

    return {"status": "resumed"}


@app.post("/api/documents/{sessionId}/approve")
async def approve_document(sessionId: str):
    config = {"configurable": {"thread_id": sessionId}}
    state_info = await app_graph.aget_state(config)

    if not state_info or not state_info.values:
        raise HTTPException(status_code=404, detail="Session thread not found.")

    await app_graph.aupdate_state(config, {
        "feedback": None,
        "scorecard": Scorecard(
            score=100,
            checks=[
                AuditCheck(id="sec", name="Security Layer",   status="verified"),
                AuditCheck(id="sov", name="Data Sovereignty", status="verified"),
                AuditCheck(id="tok", name="Token Handling",   status="verified"),
                AuditCheck(id="rat", name="Rate Limiting",    status="verified"),
            ],
            summary="Approved by human reviewer."
        ),
        "status": "completed"
    })

    await app_graph.ainvoke(None, config=config)
    return {"status": "approved"}


@app.get("/api/documents/{sessionId}/stream")
async def stream_document_updates(sessionId: str):
    """
    SSE endpoint — streams the real LangGraph checkpoint state to the frontend.
    Polls until status is 'paused' or 'completed', then stops.
    No simulation. No fake data. Just the real checkpoint.
    """
    async def sse_generator():
        config = {"configurable": {"thread_id": sessionId}}

        yield {
            "event": "connection",
            "data": json.dumps({"status": "connected", "sessionId": sessionId})
        }

        last_state_values = None

        for _ in range(90):  # poll up to 90 seconds
            state_info = await app_graph.aget_state(config)

            if not state_info or not state_info.values:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "Session state unavailable"})
                }
                return

            last_state_values = state_info.values
            current_status = last_state_values.get("status")

            # If graph is paused at interrupt point, status may still say "running"
            # Fix it: check if next node is human_arbitration_node
            if (current_status == "running"
                    and state_info.next
                    and "human_arbitration_node" in state_info.next):
                await app_graph.aupdate_state(config, {"status": "paused"})
                last_state_values = {**last_state_values, "status": "paused"}
                current_status = "paused"

            yield {
                "event": "message",
                "data": to_json(last_state_values)
            }

            if current_status in ("paused", "completed"):
                return

            await asyncio.sleep(1.0)

    return EventSourceResponse(sse_generator())