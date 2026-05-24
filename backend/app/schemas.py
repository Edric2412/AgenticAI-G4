from pydantic import BaseModel
from typing import List, Optional

class AuditCheck(BaseModel):
    id: str
    name: str
    status: str  # "verified" | "attention" | "pending"

class Scorecard(BaseModel):
    score: int
    checks: List[AuditCheck]
    summary: str

class TraceStep(BaseModel):
    id: str
    name: str
    description: str
    status: str  # "completed" | "active" | "pending"
    timestamp: Optional[str] = None
    progress: Optional[int] = None

# Input Requests
class CreateDocumentRequest(BaseModel):
    archetype: str  # "Technical" | "Legal" | "Financial" | "Creative"
    payloadText: str
    loopGuard: int = 3
    semanticEnrichment: bool = True
    conflictDetection: bool = False

class FeedbackRequest(BaseModel):
    feedback: str

# Response Models
class DocumentSessionResponse(BaseModel):
    sessionId: str
    archetype: str
    documentContent: str
    status: str  # "idle" | "running" | "paused" | "completed" | "error"
    loopCount: int
    maxLoops: int
    scorecard: Scorecard
    trace: List[TraceStep]
