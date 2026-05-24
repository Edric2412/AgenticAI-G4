import asyncio
import json
import uuid
from fastapi import FastAPI, HTTPException, Request
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

# CORS Middlewares to enable cross-origin Next.js client requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory dictionary for keeping track of initial configurations (like maxLoops, payloadText, etc.)
# since MemorySaver checkpoints the graph states natively
session_configs = {}

@app.post("/api/documents", status_code=201)
async def create_document(request: CreateDocumentRequest):
    """
    1. Initialize a new document session.
    2. Start the LangGraph workflow thread.
    3. Return the sessionId (thread_id).
    """
    session_id = f"dfl_{uuid.uuid4().hex[:9]}"
    
    # Store settings in memory
    session_configs[session_id] = {
        "maxLoops": request.loopGuard,
        "archetype": request.archetype,
        "payloadText": request.payloadText
    }
    
    # Construct initial state
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
                AuditCheck(id="sec", name="Security Layer", status="pending"),
                AuditCheck(id="sov", name="Data Sovereignty", status="pending"),
                AuditCheck(id="tok", name="Token Handling", status="pending"),
                AuditCheck(id="rat", name="Rate Limiting", status="pending"),
            ],
            summary="Awaiting analysis initialization."
        ),
        "trace": [
            TraceStep(id="1", name="Context Analysis", description="Analyzing inputs...", status="pending"),
            TraceStep(id="2", name="Architecture Mapping", description="Mapping nodes...", status="pending"),
            TraceStep(id="3", name="PRD Synthesis", description="Preparing drafting compiler...", status="pending"),
            TraceStep(id="4", name="Validation Check", description="Awaiting draft...", status="pending"),
        ],
        "payloadText": request.payloadText,
        "feedback": None,
        "current_step": "init"
    }
    
    # Config for LangGraph thread persistence
    config = {"configurable": {"thread_id": session_id}}
    
    # Invoke initial nodes (runs until first HITL interrupt_before human_arbitration_node)
    await app_graph.ainvoke(initial_state, config=config)
    
    return {"sessionId": session_id}


@app.get("/api/documents/{sessionId}")
async def get_document_state(sessionId: str):
    """
    Fetch current session state from the LangGraph checkpointer.
    """
    config = {"configurable": {"thread_id": sessionId}}
    state_info = await app_graph.aget_state(config)
    
    if not state_info or not state_info.values:
        raise HTTPException(status_code=404, detail="Document session not found.")
        
    return state_info.values


@app.post("/api/documents/{sessionId}/feedback")
async def submit_revision_feedback(sessionId: str, request: FeedbackRequest):
    """
    Resume LangGraph flow with user feedback revision requests.
    """
    config = {"configurable": {"thread_id": sessionId}}
    state_info = await app_graph.aget_state(config)
    
    if not state_info or not state_info.values:
        raise HTTPException(status_code=404, detail="Session thread not found.")
        
    current_state = state_info.values
    current_loops = current_state.get("loopCount", 0)
    
    # Update State with feedback values and increment loop index
    updated_values = {
        "feedback": request.feedback,
        "loopCount": current_loops + 1,
        "status": "running"
    }
    
    # Update state in checkpoint
    await app_graph.aupdate_state(config, updated_values)
    
    # Resume run (runs until next interrupt gate or end)
    await app_graph.ainvoke(None, config=config)
    
    return {"status": "resumed"}


@app.post("/api/documents/{sessionId}/approve")
async def approve_document(sessionId: str):
    """
    Finalize approval, bypass router checks, and route straight to completed state.
    """
    config = {"configurable": {"thread_id": sessionId}}
    state_info = await app_graph.aget_state(config)
    
    if not state_info or not state_info.values:
        raise HTTPException(status_code=404, detail="Session thread not found.")
        
    # Clear feedbacks, force routing parameters
    updated_values = {
        "feedback": None,
        "scorecard": Scorecard(
            score=100,  # Forces router edge to transition to deploy
            checks=[
                AuditCheck(id="sec", name="Security Layer", status="verified"),
                AuditCheck(id="sov", name="Data Sovereignty", status="verified"),
                AuditCheck(id="tok", name="Token Handling", status="verified"),
                AuditCheck(id="rat", name="Rate Limiting", status="verified")
            ],
            summary="Approved by human reviewer."
        ),
        "status": "completed"
    }
    
    await app_graph.aupdate_state(config, updated_values)
    
    # Run graph to final completion node
    await app_graph.ainvoke(None, config=config)
    
    return {"status": "approved"}


@app.get("/api/documents/{sessionId}/stream")
async def stream_document_updates(sessionId: str):
    """
    SSE stream endpoint. Delivers live state transitions and token emissions.
    """
    async def sse_generator():
      config = {"configurable": {"thread_id": sessionId}}
      
      # Yield connections logs
      yield {
          "event": "connection",
          "data": json.dumps({"status": "connected", "sessionId": sessionId})
      }
      
      # Retrieve current state snapshot
      state_info = await app_graph.aget_state(config)
      if not state_info or not state_info.values:
          yield {
              "event": "error",
              "data": json.dumps({"error": "Session state unavailable"})
          }
          return
          
      current_state = state_info.values
      
      # Yield current baseline state first
      yield {
          "event": "message",
          "data": json.dumps(current_state)
      }
      
      # If status is running, we simulate token generation and state transition deltas.
      # This provides full-fidelity simulation feedback to frontend clients.
      if current_state.get("status") == "running":
          await asyncio.sleep(1.0)
          
          # Simulate processing logs
          for step_idx, step_name in enumerate(["Context Analysis", "Architecture Mapping", "PRD Synthesis"]):
              await asyncio.sleep(0.5)
              
              # Transition state
              current_state["trace"][step_idx]["status"] = "completed"
              if step_idx < 2:
                  current_state["trace"][step_idx + 1]["status"] = "active"
                  
              yield {
                  "event": "message",
                  "data": json.dumps(current_state)
              }
          
          # Transition scorecard Critic checks
          await asyncio.sleep(1.0)
          
          loop = current_state.get("loopCount", 0)
          if loop == 0:
              current_state["scorecard"] = Scorecard(
                  score=88,
                  checks=[
                      AuditCheck(id="sec", name="Security Layer", status="verified"),
                      AuditCheck(id="sov", name="Data Sovereignty", status="verified"),
                      AuditCheck(id="tok", name="Token Handling", status="attention"),
                      AuditCheck(id="rat", name="Rate Limiting", status="pending"),
                  ],
                  summary="Critic flagged missing Rate Limiting specs and ambiguous Token Handling protocols."
              )
          else:
              current_state["scorecard"] = Scorecard(
                  score=98,
                  checks=[
                      AuditCheck(id="sec", name="Security Layer", status="verified"),
                      AuditCheck(id="sov", name="Data Sovereignty", status="verified"),
                      AuditCheck(id="tok", name="Token Handling", status="verified"),
                      AuditCheck(id="rat", name="Rate Limiting", status="verified"),
                  ],
                  summary="Critic check verified. Rate Limiting and Token Handling meet design requirements."
              )
              
          current_state["status"] = "paused"
          current_state["trace"][3]["status"] = "completed"
          
          # Write updated values to state checkpoint so GET calls return matched status
          await app_graph.aupdate_state(config, {
              "scorecard": current_state["scorecard"],
              "status": "paused",
              "trace": current_state["trace"]
          })
          
          yield {
              "event": "message",
              "data": json.dumps(current_state)
          }

    return EventSourceResponse(sse_generator())
