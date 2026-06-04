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
    TraceStep,
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


def to_json(obj) -> str:
    """Serialize state dict — converts Pydantic objects via model_dump()."""
    return json.dumps(
        obj,
        default=lambda o: o.model_dump() if hasattr(o, "model_dump") else str(o),
    )


@app.post("/api/documents", status_code=201)
async def create_document(request: CreateDocumentRequest):
    session_id = f"dfl_{uuid.uuid4().hex[:9]}"

    session_configs[session_id] = {
        "maxLoops": request.loopGuard,
        "archetype": request.archetype,
        "payloadText": request.payloadText,
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
            summary="Awaiting analysis initialization.",
        ),
        "trace": [
            TraceStep(id="1", name="Context Analysis",     description="Analyzing inputs...",             status="pending"),
            TraceStep(id="2", name="Architecture Mapping", description="Mapping nodes...",                status="pending"),
            TraceStep(id="3", name="PRD Synthesis",        description="Preparing drafting compiler...", status="pending"),
            TraceStep(id="4", name="Validation Check",     description="Awaiting draft...",              status="pending"),
        ],
        "payloadText": request.payloadText,
        "feedback": None,
        "current_step": "init",
    }

    config = {"configurable": {"thread_id": session_id}}
    await app_graph.ainvoke(initial_state, config=config)

    # LangGraph pauses BEFORE human_arbitration_node (interrupt_before).
    # That node never runs on first pass, so status stays "running".
    # We manually set it to "paused" so the frontend enables the action buttons.
    state_info = await app_graph.aget_state(config)
    if (
        state_info
        and state_info.next
        and "human_arbitration_node" in state_info.next
    ):
        await app_graph.aupdate_state(config, {"status": "paused"})

    return {"sessionId": session_id}


@app.api_route("/api/documents/{sessionId}", methods=["GET", "HEAD"])
async def get_document_state(sessionId: str, request: Request):
    # HEAD used by frontend to check if backend is alive
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

    await app_graph.aupdate_state(
        config,
        {
            "feedback": request.feedback,
            "loopCount": current_loops + 1,
            "status": "running",
        },
    )

    # Resume graph — runs human_arbitration_node, then route_after_arbitration
    # routes to writer_node because feedback is set
    await app_graph.ainvoke(None, config=config)

    # After revision, graph pauses again at interrupt_before — set paused
    state_info = await app_graph.aget_state(config)
    if (
        state_info
        and state_info.next
        and "human_arbitration_node" in state_info.next
    ):
        await app_graph.aupdate_state(config, {"status": "paused"})

    return {"status": "resumed"}


@app.post("/api/documents/{sessionId}/approve")
async def approve_document(sessionId: str):
    config = {"configurable": {"thread_id": sessionId}}
    state_info = await app_graph.aget_state(config)

    if not state_info or not state_info.values:
        raise HTTPException(status_code=404, detail="Session thread not found.")

    # Force score to 100 — route_after_arbitration will send to deployment_node
    await app_graph.aupdate_state(
        config,
        {
            "feedback": None,
            "scorecard": Scorecard(
                score=100,
                checks=[
                    AuditCheck(id="sec", name="Security Layer",   status="verified"),
                    AuditCheck(id="sov", name="Data Sovereignty", status="verified"),
                    AuditCheck(id="tok", name="Token Handling",   status="verified"),
                    AuditCheck(id="rat", name="Rate Limiting",    status="verified"),
                ],
                summary="Approved by human reviewer.",
            ),
            "status": "running",
        },
    )

    # Resume graph — human_arbitration_node runs, then routes to deployment_node
    await app_graph.ainvoke(None, config=config)

    return {"status": "approved"}


@app.get("/api/documents/{sessionId}/stream")
async def stream_document_updates(sessionId: str):
    """
    SSE endpoint — streams real LangGraph checkpoint state to the frontend.
    Polls until status is 'paused' or 'completed', then closes.
    """
    async def sse_generator():
        config = {"configurable": {"thread_id": sessionId}}

        yield {
            "event": "connection",
            "data": json.dumps({"status": "connected", "sessionId": sessionId}),
        }

        for _ in range(90):  # poll for up to 90 seconds
            state_info = await app_graph.aget_state(config)

            if not state_info or not state_info.values:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "Session state unavailable"}),
                }
                return

            current_status = state_info.values.get("status")

            # Safety net: if still running but graph is at interrupt point, fix status
            if (
                current_status == "running"
                and state_info.next
                and "human_arbitration_node" in state_info.next
            ):
                await app_graph.aupdate_state(config, {"status": "paused"})
                current_status = "paused"

            yield {
                "event": "message",
                "data": to_json(state_info.values),
            }

            if current_status in ("paused", "completed"):
                return

            await asyncio.sleep(1.0)

    return EventSourceResponse(sse_generator())