from typing import TypedDict, List, Optional
from app.schemas import Scorecard, TraceStep

class DocumentState(TypedDict):
    # Public state variables matching frontend properties
    sessionId: str
    archetype: str
    documentContent: str
    status: str  # "idle" | "running" | "paused" | "completed" | "error"
    loopCount: int
    maxLoops: int
    scorecard: Scorecard
    trace: List[TraceStep]
    
    # Inputs & payload configurations
    payloadText: str
    feedback: Optional[str]
    semanticEnrichment: Optional[bool]
    conflictDetection: Optional[bool]
    
    # Internal helper state
    current_step: Optional[str]
