import asyncio
import json
import uuid
from fastapi import FastAPI, HTTPException, Request, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from sqlalchemy import select

from app.schemas import (
    CreateDocumentRequest,
    FeedbackRequest,
    DocumentSessionResponse,
    Scorecard,
    AuditCheck,
    TraceStep,
    get_default_checks,
    get_verified_checks,
)
from app.graph import app_graph
from app.state import DocumentState

app = FastAPI(title="DocuFlow AI Backend Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_configs = {}

@app.on_event("startup")
async def startup_event():
    from app.db import Base, engine
    if engine:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("Database tables initialized successfully.")
        except Exception as e:
            print(f"Database table initialization failed: {e}")

async def persist_session_state(session_id: str):
    from app.db import AsyncSessionLocal, SessionState
    
    if not AsyncSessionLocal:
        return

    config = {"configurable": {"thread_id": session_id}}
    state_info = await app_graph.aget_state(config)
    if not state_info or not state_info.values:
        return

    values = state_info.values
    scorecard_dict = None
    if values.get("scorecard"):
        scorecard = values.get("scorecard")
        scorecard_dict = scorecard.model_dump() if hasattr(scorecard, "model_dump") else scorecard

    trace_list = []
    if values.get("trace"):
        trace = values.get("trace")
        trace_list = [t.model_dump() if hasattr(t, "model_dump") else t for t in trace]

    async with AsyncSessionLocal() as session:
        try:
            db_state = await session.get(SessionState, session_id)
            if not db_state:
                db_state = SessionState(session_id=session_id)
                session.add(db_state)
            
            db_state.archetype = values.get("archetype", "Technical")
            db_state.document_content = values.get("documentContent", "")
            db_state.status = values.get("status", "idle")
            db_state.loop_count = values.get("loopCount", 0)
            db_state.max_loops = values.get("maxLoops", 3)
            db_state.payload_text = values.get("payloadText", "")
            db_state.feedback = values.get("feedback", "")
            db_state.current_step = values.get("current_step", "init")
            db_state.scorecard = scorecard_dict
            db_state.trace = trace_list

            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"Failed to persist session state: {e}")
        except BaseException:
            await session.rollback()
            raise


def to_json(obj) -> str:
    """Serialize state dict — converts Pydantic objects via model_dump()."""
    return json.dumps(
        obj,
        default=lambda o: o.model_dump() if hasattr(o, "model_dump") else str(o),
    )


@app.get("/api/documents")
async def list_documents_and_metrics():
    from app.db import AsyncSessionLocal, SessionState
    from app.schemas import Scorecard, TraceStep

    registry = []
    awaiting_action = 0
    generated_count = 0
    total_loops = 0

    if AsyncSessionLocal:
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(SessionState))
                db_states = result.scalars().all()
                
                for db_state in db_states:
                    status = db_state.status
                    loop_count = db_state.loop_count
                    total_loops += loop_count

                    if status == "running":
                        display_status = "In Agentic Loop"
                    elif status == "paused":
                        display_status = "Awaiting Review"
                        awaiting_action += 1
                    elif status == "completed":
                        display_status = "Verified"
                        generated_count += 1
                    else:
                        display_status = "Awaiting Review"

                    agent_name = "Summarizer-Alpha"
                    if db_state.current_step == "critic" or loop_count > 0:
                        agent_name = "Compliance-Bot"
                    elif status == "completed":
                        agent_name = "Fiscal-Analytic-02"

                    doc_content = db_state.document_content or ""
                    doc_name = f"{db_state.archetype} Document Synthesis"
                    if doc_content:
                        for line in doc_content.split("\n"):
                            if line.startswith("# "):
                                doc_name = line.replace("# ", "").strip()
                                break

                    elapsed_sec = (loop_count * 95) + 42
                    elapsed = f"{elapsed_sec // 60:02d}:{elapsed_sec % 60:02d}"

                    registry.append({
                        "id": db_state.session_id,
                        "name": doc_name,
                        "uuid": db_state.session_id.upper(),
                        "agent": agent_name,
                        "status": display_status,
                        "elapsed": elapsed
                    })
                    
                    # Lazy-load back into memory checkpointer if server restarted
                    config = {"configurable": {"thread_id": db_state.session_id}}
                    checkpointer = app_graph.checkpointer
                    if hasattr(checkpointer, "storage") and db_state.session_id not in checkpointer.storage:
                        scorecard_obj = Scorecard(**db_state.scorecard) if db_state.scorecard else None
                        trace_obj_list = [TraceStep(**t) for t in db_state.trace] if db_state.trace else []
                        
                        has_conflict_check = False
                        if db_state.scorecard and "checks" in db_state.scorecard:
                            checks_list = db_state.scorecard["checks"]
                            has_conflict_check = any(c.get("id") == "con" for c in checks_list if isinstance(c, dict))
                        
                        state_val = {
                            "sessionId": db_state.session_id,
                            "archetype": db_state.archetype,
                            "documentContent": db_state.document_content,
                            "status": db_state.status,
                            "loopCount": db_state.loop_count,
                            "maxLoops": db_state.max_loops,
                            "scorecard": scorecard_obj,
                            "trace": trace_obj_list,
                            "payloadText": db_state.payload_text,
                            "feedback": db_state.feedback,
                            "current_step": db_state.current_step,
                            "semanticEnrichment": True,
                            "conflictDetection": has_conflict_check,
                        }
                        await app_graph.aupdate_state(config, state_val)
        except Exception as e:
            print(f"Failed to query persistent session states: {e}")

    # Fallback to checkpointer storage if DB is not used or empty
    if not registry:
        checkpointer = app_graph.checkpointer
        thread_ids = list(checkpointer.storage.keys()) if hasattr(checkpointer, "storage") else []
        for thread_id in thread_ids:
            config = {"configurable": {"thread_id": thread_id}}
            state_info = await app_graph.aget_state(config)
            if not state_info or not state_info.values:
                continue

            values = state_info.values
            status = values.get("status", "idle")
            loop_count = values.get("loopCount", 0)
            total_loops += loop_count

            if status == "running":
                display_status = "In Agentic Loop"
            elif status == "paused":
                display_status = "Awaiting Review"
                awaiting_action += 1
            elif status == "completed":
                display_status = "Verified"
                generated_count += 1
            else:
                display_status = "Awaiting Review"

            agent_name = "Summarizer-Alpha"
            if values.get("current_step") == "critic" or loop_count > 0:
                agent_name = "Compliance-Bot"
            elif status == "completed":
                agent_name = "Fiscal-Analytic-02"

            doc_content = values.get("documentContent", "")
            doc_name = f"{values.get('archetype', 'Technical')} Document Synthesis"
            if doc_content:
                for line in doc_content.split("\n"):
                    if line.startswith("# "):
                        doc_name = line.replace("# ", "").strip()
                        break

            elapsed_sec = (loop_count * 95) + 42
            elapsed = f"{elapsed_sec // 60:02d}:{elapsed_sec % 60:02d}"

            registry.append({
                "id": thread_id,
                "name": doc_name,
                "uuid": thread_id.upper(),
                "agent": agent_name,
                "status": display_status,
                "elapsed": elapsed
            })

    if not registry:
        metrics = {
            "awaitingAction": 0,
            "generatedCount": 0,
            "avgRuntime": "--",
            "efficiencySurge": "0h"
        }
    else:
        avg_runtime_sec = int((total_loops * 95 + len(registry) * 42) / len(registry))
        metrics = {
            "awaitingAction": awaiting_action,
            "generatedCount": generated_count,
            "avgRuntime": f"{avg_runtime_sec // 60}m {avg_runtime_sec % 60}s",
            "efficiencySurge": f"{len(registry) * 2}h"
        }

    return {
        "metrics": metrics,
        "registry": registry
    }


@app.post("/api/documents", status_code=201)
async def create_document(request: CreateDocumentRequest, background_tasks: BackgroundTasks):
    session_id = f"dfl_{uuid.uuid4().hex[:9]}"

    session_configs[session_id] = {
        "maxLoops": request.loopGuard,
        "archetype": request.archetype,
        "payloadText": request.payloadText,
        "semanticEnrichment": request.semanticEnrichment,
        "conflictDetection": request.conflictDetection,
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
                AuditCheck(**c) for c in get_default_checks(request.archetype, request.conflictDetection)
            ],
            summary="Awaiting analysis initialization.",
        ),
        "trace": [
            TraceStep(id="1", name="Context Analysis",     description="Analyzing inputs...",             status="active"),
            TraceStep(id="2", name="Architecture Mapping", description="Mapping nodes...",                status="pending"),
            TraceStep(id="3", name="PRD Synthesis",        description="Preparing drafting compiler...", status="pending"),
            TraceStep(id="4", name="Validation Check",     description="Awaiting draft...",              status="pending"),
        ],
        "payloadText": request.payloadText,
        "feedback": None,
        "semanticEnrichment": request.semanticEnrichment,
        "conflictDetection": request.conflictDetection,
        "current_step": "init",
    }


    config = {"configurable": {"thread_id": session_id}}

    # Pre-populate state checkpointer so frontend HEAD check immediately succeeds
    await app_graph.aupdate_state(config, initial_state)
    await persist_session_state(session_id)

    async def run_graph_async():
        await app_graph.ainvoke(None, config=config)
        state_info = await app_graph.aget_state(config)
        if (
            state_info
            and state_info.next
            and "human_arbitration_node" in state_info.next
        ):
            await app_graph.aupdate_state(config, {"status": "paused"})
        await asyncio.shield(persist_session_state(session_id))

    background_tasks.add_task(run_graph_async)

    return {"sessionId": session_id}


@app.api_route("/api/documents/{sessionId}", methods=["GET", "HEAD"])
async def get_document_state(sessionId: str, request: Request):
    config = {"configurable": {"thread_id": sessionId}}
    state_info = await app_graph.aget_state(config)

    if not state_info or not state_info.values:
        from app.db import AsyncSessionLocal, SessionState
        from app.schemas import Scorecard, TraceStep
        if AsyncSessionLocal:
            try:
                async with AsyncSessionLocal() as session:
                    db_state = await session.get(SessionState, sessionId)
                    if db_state:
                        scorecard_obj = Scorecard(**db_state.scorecard) if db_state.scorecard else None
                        trace_obj_list = [TraceStep(**t) for t in db_state.trace] if db_state.trace else []
                        
                        has_conflict_check = False
                        if db_state.scorecard and "checks" in db_state.scorecard:
                            checks_list = db_state.scorecard["checks"]
                            has_conflict_check = any(c.get("id") == "con" for c in checks_list if isinstance(c, dict))
                        
                        state_val = {
                            "sessionId": db_state.session_id,
                            "archetype": db_state.archetype,
                            "documentContent": db_state.document_content,
                            "status": db_state.status,
                            "loopCount": db_state.loop_count,
                            "maxLoops": db_state.max_loops,
                            "scorecard": scorecard_obj,
                            "trace": trace_obj_list,
                            "payloadText": db_state.payload_text,
                            "feedback": db_state.feedback,
                            "current_step": db_state.current_step,
                            "semanticEnrichment": True,
                            "conflictDetection": has_conflict_check,
                        }
                        await app_graph.aupdate_state(config, state_val)
                        state_info = await app_graph.aget_state(config)
            except Exception as e:
                print(f"Failed to load session state from DB: {e}")

    if not state_info or not state_info.values:
        raise HTTPException(status_code=404, detail="Document session not found.")

    if request.method == "HEAD":
        return Response(status_code=200)

    return json.loads(to_json(state_info.values))


@app.post("/api/documents/{sessionId}/feedback")
async def submit_revision_feedback(sessionId: str, request: FeedbackRequest, background_tasks: BackgroundTasks):
    config = {"configurable": {"thread_id": sessionId}}
    state_info = await app_graph.aget_state(config)

    if not state_info or not state_info.values:
        raise HTTPException(status_code=404, detail="Session thread not found.")

    current_loops = state_info.values.get("loopCount", 0)

    # Reset trace steps for revision loop visualization
    trace = list(state_info.values.get("trace", []))
    if len(trace) >= 4:
        trace[2] = TraceStep(id="3", name="PRD Synthesis", description="Amending requirements based on feedback...", status="active", progress=50)
        trace[3] = TraceStep(id="4", name="Validation Check", description="Awaiting draft validation...", status="pending")

    await app_graph.aupdate_state(
        config,
        {
            "feedback": request.feedback,
            "loopCount": current_loops + 1,
            "status": "running",
            "trace": trace,
        },
    )
    await persist_session_state(sessionId)

    async def resume_graph_async():
        await app_graph.ainvoke(None, config=config)
        state_info_new = await app_graph.aget_state(config)
        if (
            state_info_new
            and state_info_new.next
            and "human_arbitration_node" in state_info_new.next
        ):
            await app_graph.aupdate_state(config, {"status": "paused"})
        await asyncio.shield(persist_session_state(sessionId))

    background_tasks.add_task(resume_graph_async)

    return {"status": "resumed"}


@app.post("/api/documents/{sessionId}/approve")
async def approve_document(sessionId: str, background_tasks: BackgroundTasks):
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
                    AuditCheck(**c) for c in get_verified_checks(
                        state_info.values.get("archetype", "Technical"),
                        state_info.values.get("conflictDetection", False)
                    )
                ],
                summary="Approved by human reviewer.",
            ),
            "status": "running",
        },
    )
    await persist_session_state(sessionId)

    async def approve_graph_async():
        await app_graph.ainvoke(None, config=config)
        await asyncio.shield(persist_session_state(sessionId))

    background_tasks.add_task(approve_graph_async)

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
                await asyncio.shield(persist_session_state(sessionId))

            yield {
                "event": "message",
                "data": to_json(state_info.values),
            }

            if current_status in ("paused", "completed"):
                return

            await asyncio.sleep(1.0)

    return EventSourceResponse(sse_generator())